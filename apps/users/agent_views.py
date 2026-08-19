from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .agent_serializers import (
    AgentCreateSerializer,
    AgentSerializer,
    AgentUpdateSerializer,
)
from .models import Agent


class IsAdminUserRole(IsAuthenticated):
    """
    Permission personnalisée réservée aux administrateurs.

    L'utilisateur doit être authentifié avec un token JWT valide
    et posséder le rôle `admin`.
    """

    def has_permission(self, request, view):
        """
        Vérifie que la requête est authentifiée et que l'utilisateur
        possède le rôle administrateur.
        """
        return (
            super().has_permission(request, view)
            and request.user.role == "admin"
        )


class AgentListCreateView(APIView):
    """
    GET  /api/agents/     — liste des agents
    POST /api/agents/     — crée un agent
    """

    permission_classes = [IsAdminUserRole]

    def get(self, request):
        """
        Retourne la liste des agents.

        Les comptes Utilisateur associés sont chargés avec `select_related`
        afin d'éviter des requêtes SQL supplémentaires.
        """
        agents = (
            Agent.objects
            .select_related("utilisateur")
            .order_by("matricule")
        )

        serializer = AgentSerializer(agents, many=True)

        return Response(serializer.data)

    @extend_schema(
        request=AgentCreateSerializer,
        responses={201: AgentSerializer},
    )
    def post(self, request):
        serializer = AgentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        agent = serializer.save()

        output = AgentSerializer(agent)

        return Response(
            output.data,
            status=status.HTTP_201_CREATED,
        )


class AgentDetailView(APIView):
    """
    GET    /api/agents/<id>/  — détail d'un agent
    PATCH  /api/agents/<id>/  — modification partielle
    DELETE /api/agents/<id>/  — suppression
    """

    permission_classes = [IsAdminUserRole]

    def get_agent(self, pk):
        """
        Recherche un agent par son identifiant primaire.

        Retourne l'agent avec son utilisateur associé ou None
        si aucun agent ne correspond à l'identifiant fourni.
        """
        return (
            Agent.objects
            .select_related("utilisateur")
            .filter(pk=pk)
            .first()
        )

    def get(self, request, pk):
        agent = self.get_agent(pk)

        if agent is None:
            return Response(
                {"detail": "Agent introuvable."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = AgentSerializer(agent)

        return Response(serializer.data)

    @extend_schema(
        request=AgentUpdateSerializer,
        responses={200: AgentSerializer},
    )
    def patch(self, request, pk):
        agent = self.get_agent(pk)

        if agent is None:
            return Response(
                {"detail": "Agent introuvable."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # -------------------------
        # Champs du modèle Agent
        # -------------------------

        agent_fields = {
            "matricule",
            "departement",
            "specialisation",
            "disponible",
            "score_satisfaction",
            "taux_completion",
            "ponctualite",
            "taches_resolues_semaine",
            "objectif_hebdo",
        }

        agent_data = {
            key: value
            for key, value in request.data.items()
            if key in agent_fields
        }

        # -------------------------
        # Champs du modèle Utilisateur
        # -------------------------

        user_fields = {
            "nom_complet",
            "email",
            "telephone",
        }

        user_data = {
            key: value
            for key, value in request.data.items()
            if key in user_fields
        }

        with transaction.atomic():

            # -------------------------
            # Nom complet
            # -------------------------

            if "nom_complet" in user_data:
                nom_complet = user_data["nom_complet"].strip()

                if not nom_complet:
                    return Response(
                        {
                            "nom_complet": [
                                "Le nom complet est obligatoire."
                            ]
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                parts = nom_complet.split(" ", 1)

                agent.utilisateur.first_name = parts[0]
                agent.utilisateur.last_name = (
                    parts[1] if len(parts) > 1 else ""
                )

            # -------------------------
            # Email
            # -------------------------

            if "email" in user_data:
                email = user_data["email"].strip()

                if (
                    agent.utilisateur.email.lower() != email.lower()
                    and agent.utilisateur.__class__.objects.filter(
                        email__iexact=email
                    )
                    .exclude(pk=agent.utilisateur.pk)
                    .exists()
                ):
                    return Response(
                        {
                            "email": [
                                "Cette adresse email est déjà utilisée."
                            ]
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                agent.utilisateur.email = email

            # -------------------------
            # Téléphone
            # -------------------------

            if "telephone" in user_data:
                telephone = user_data["telephone"]

                if telephone and agent.utilisateur.__class__.objects.filter(
                    telephone=telephone
                ).exclude(pk=agent.utilisateur.pk).exists():
                    return Response(
                        {
                            "telephone": [
                                "Ce numéro de téléphone est déjà utilisé."
                            ]
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                agent.utilisateur.telephone = telephone or None

            # Sauvegarde Utilisateur
            if user_data:
                agent.utilisateur.save()

            # -------------------------
            # Matricule
            # -------------------------

            if "matricule" in agent_data:
                matricule = agent_data["matricule"]

                if (
                    Agent.objects.filter(matricule=matricule)
                    .exclude(pk=agent.pk)
                    .exists()
                ):
                    return Response(
                        {
                            "matricule": [
                                "Ce matricule est déjà utilisé."
                            ]
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            # -------------------------
            # Mise à jour Agent
            # -------------------------

            for field, value in agent_data.items():
                setattr(agent, field, value)

            if agent_data:
                agent.save()

        return Response(AgentSerializer(agent).data)

    def delete(self, request, pk):
        agent = self.get_agent(pk)

        if agent is None:
            return Response(
                {"detail": "Agent introuvable."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # La suppression de Agent supprime également
        # l'utilisateur associé grâce au OneToOne + CASCADE.
        agent.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)