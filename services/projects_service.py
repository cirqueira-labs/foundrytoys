from typing import Any, Dict, Iterable, Optional, Tuple

from services.repository import (
    AzureProjectsRepository,
    FileInfo,
    ProjectsRepository,
    VectorStoreInfo,
)


class ProjectsService:
    def __init__(self) -> None:
        self._repo: Optional[ProjectsRepository] = None
        self.vector_store_id: Optional[str] = None
        self.vector_store_name: Optional[str] = None

    def set_client(self, client: Any) -> None:
        self._repo = AzureProjectsRepository(client)

    def set_repository(self, repo: ProjectsRepository) -> None:
        self._repo = repo

    def set_vector_store(self, vs: VectorStoreInfo | Any) -> None:
        if isinstance(vs, VectorStoreInfo):
            self.vector_store_id = vs.id
            self.vector_store_name = vs.name
        else:
            self.vector_store_id = getattr(vs, "id", None)
            self.vector_store_name = getattr(vs, "name", None)

    def has_client(self) -> bool:
        return self._repo is not None

    def list_vector_stores(self) -> Iterable[VectorStoreInfo]:
        if not self._repo:
            raise RuntimeError("Cliente do projeto não inicializado.")
        return list(self._repo.list_vector_stores())

    def list_vector_store_files(self) -> Dict[str, FileInfo]:
        if not self._repo:
            raise RuntimeError("Cliente do projeto não inicializado.")
        if not self.vector_store_id:
            raise RuntimeError("Nenhum Vector Store selecionado.")
        files = list(self._repo.list_vector_store_files(self.vector_store_id))
        return {f.id: f for f in files}

    def upload_and_attach_file(self, file_path: str) -> Tuple[bool, str]:
        if not self._repo:
            return False, "Cliente do projeto não inicializado."
        if not self.vector_store_id:
            return False, "Nenhum Vector Store selecionado."
        try:
            self._repo.upload_file_to_vector_store(self.vector_store_id, file_path)
            return True, "Arquivo anexado com sucesso."
        except Exception as e:  # noqa: BLE001
            return False, f"Erro ao anexar arquivo: {e}"
