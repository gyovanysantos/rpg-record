import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Users, Plus, Trash2, ChevronRight, Loader2 } from "lucide-react";
import {
  useCharacters,
  useCreateCharacter,
  useDeleteCharacter,
  type CharacterSummary,
} from "../hooks/useCharacters";

export default function CharactersPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { data: characters, isLoading, error } = useCharacters();
  const createMut = useCreateCharacter();
  const deleteMut = useDeleteCharacter();

  const [confirmDelete, setConfirmDelete] = useState<CharacterSummary | null>(null);

  const handleCreate = () => {
    createMut.mutate(
      { name: "New Hero" },
      {
        onSuccess: (data) => {
          navigate(`/characters/${encodeURIComponent(data.filename)}`);
        },
      }
    );
  };

  const handleDelete = (char: CharacterSummary) => {
    setConfirmDelete(char);
  };

  const confirmDeleteAction = () => {
    if (!confirmDelete) return;
    deleteMut.mutate(confirmDelete.filename, {
      onSettled: () => setConfirmDelete(null),
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Users className="text-accent" size={28} />
          <h1 className="text-2xl font-display text-accent">
            {t("characters.title")}
          </h1>
        </div>
        <button
          className="btn-primary flex items-center gap-2"
          onClick={handleCreate}
          disabled={createMut.isPending}
        >
          {createMut.isPending ? (
            <Loader2 size={16} className="animate-spin" />
          ) : (
            <Plus size={16} />
          )}
          {t("characters.newCharacter")}
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-danger/20 border border-danger text-danger rounded-lg p-4">
          {t("characters.loadError", "Erro ao carregar personagens.")}
        </div>
      )}

      {/* Loading */}
      {isLoading && (
        <div className="flex justify-center py-12">
          <Loader2 size={32} className="animate-spin text-accent" />
        </div>
      )}

      {/* Character list */}
      {!isLoading && characters && characters.length === 0 && (
        <div className="card text-center py-12">
          <Users size={48} className="text-text-muted mx-auto mb-4 opacity-40" />
          <p className="text-text-muted text-lg">{t("characters.noCharacters")}</p>
          <p className="text-text-muted text-sm mt-2">
            {t("characters.clickToCreate", "Clique em \"Novo Personagem\" para começar.")}
          </p>
        </div>
      )}

      {characters && characters.length > 0 && (
        <div className="grid gap-3">
          {characters.map((char) => (
            <div
              key={char.filename}
              onClick={() => navigate(`/characters/${encodeURIComponent(char.filename)}`)}
              className="card flex items-center justify-between group hover:border-accent/30 transition-colors cursor-pointer"
            >
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-full bg-accent/20 flex items-center justify-center">
                  <span className="text-accent font-display text-lg">
                    {char.name.charAt(0).toUpperCase()}
                  </span>
                </div>
                <span className="text-text-primary text-lg font-medium">
                  {char.name}
                </span>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDelete(char);
                  }}
                  className="text-text-muted hover:text-danger transition-colors p-2 rounded-lg hover:bg-danger/10 opacity-0 group-hover:opacity-100"
                  title={t("characters.deleteCharacter")}
                >
                  <Trash2 size={16} />
                </button>
                <ChevronRight size={18} className="text-text-muted" />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Delete confirmation modal */}
      {confirmDelete && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
          <div className="bg-surface border border-border rounded-xl p-6 max-w-sm w-full mx-4 space-y-4">
            <h2 className="text-lg font-display text-danger">
              {t("characters.deleteCharacter")}
            </h2>
            <p className="text-text-primary">
              {t("characters.confirmDelete", { name: confirmDelete.name })}
            </p>
            <div className="flex justify-end gap-3">
              <button
                className="btn-ghost"
                onClick={() => setConfirmDelete(null)}
              >
                {t("common.cancel", "Cancelar")}
              </button>
              <button
                className="bg-danger text-text-primary px-4 py-2 rounded-lg hover:bg-danger-hover transition-colors"
                onClick={confirmDeleteAction}
                disabled={deleteMut.isPending}
              >
                {deleteMut.isPending ? (
                  <Loader2 size={16} className="animate-spin" />
                ) : (
                  t("characters.deleteCharacter")
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
