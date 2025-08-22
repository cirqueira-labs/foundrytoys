import logging
from typing import Optional, Tuple

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential


class ProjectClientFactory:
    def __init__(self) -> None:
        self._client: Optional[AIProjectClient] = None
        self._endpoint: Optional[str] = None

    def configure(self, endpoint: str) -> None:
        self._endpoint = endpoint
        self._client = None

    def get(self) -> AIProjectClient:
        if not self._endpoint:
            raise RuntimeError("PROJECT_ENDPOINT não está configurado.")
        if self._client is None:
            cred = DefaultAzureCredential(exclude_interactive_browser_credential=False)
            self._client = AIProjectClient(endpoint=self._endpoint, credential=cred)
        return self._client

    def get_user_info(self) -> Tuple[Optional[str], Optional[str]]:
        if not self._endpoint:
            return None, None

        try:
            cred = DefaultAzureCredential(exclude_interactive_browser_credential=False)

            organization = None
            user_name = None

            try:
                access_token = cred.get_token("https://graph.microsoft.com/.default")
                if access_token:
                    import requests

                    headers = {"Authorization": f"Bearer {access_token.token}"}

                    user_response = requests.get(
                        "https://graph.microsoft.com/v1.0/me",
                        headers=headers,
                        timeout=5,
                    )
                    if user_response.status_code == 200:
                        user_data = user_response.json()
                        user_name = user_data.get("displayName") or user_data.get(
                            "givenName"
                        )

                        if user_data.get("companyName"):
                            organization = user_data.get("companyName")

                    if not organization:
                        org_response = requests.get(
                            "https://graph.microsoft.com/v1.0/organization",
                            headers=headers,
                            timeout=5,
                        )
                        if org_response.status_code == 200:
                            org_data = org_response.json()
                            if org_data.get("value") and len(org_data["value"]) > 0:
                                org_info = org_data["value"][0]
                                organization = (
                                    org_info.get("displayName")
                                    or org_info.get("name")
                                    or org_info.get("tenantDisplayName")
                                )

                    if not organization:
                        tenant_response = requests.get(
                            "https://graph.microsoft.com/v1.0/me?$select=userPrincipalName",
                            headers=headers,
                            timeout=5,
                        )
                        if tenant_response.status_code == 200:
                            tenant_data = tenant_response.json()
                            upn = tenant_data.get("userPrincipalName", "")
                            if "@" in upn:
                                domain = upn.split("@")[1]
                                if not domain.endswith(".onmicrosoft.com"):
                                    organization = domain.split(".")[0].title()

            except Exception:
                pass

            if not organization and "/resourceGroups/" in self._endpoint:
                parts = self._endpoint.split("/")
                if "subscriptions" in parts:
                    subscription_id = parts[parts.index("subscriptions") + 1][:8]
                    organization = f"Subscription {subscription_id}"

            return user_name, organization

        except Exception as e:
            logging.warning(f"Não foi possível obter informações do usuário: {e}")
            return None, None

    def endpoint(self) -> Optional[str]:
        return self._endpoint
