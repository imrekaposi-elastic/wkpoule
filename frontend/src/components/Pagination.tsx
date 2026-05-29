import { useTranslation } from "react-i18next";

type Props = {
  page: number;
  totalPages: number;
  total: number;
  onPageChange: (page: number) => void;
  disabled?: boolean;
};

export default function Pagination({
  page,
  totalPages,
  total,
  onPageChange,
  disabled = false,
}: Props) {
  const { t } = useTranslation();

  if (totalPages <= 1 && total <= 20) {
    return null;
  }

  return (
    <nav
      className="flex flex-wrap items-center justify-center gap-3 py-4 text-sm"
      aria-label={t("pagination.label")}
    >
      <button
        type="button"
        disabled={disabled || page <= 1}
        onClick={() => onPageChange(page - 1)}
        className="rounded-md border border-gray-300 px-3 py-1.5 font-medium text-gray-800 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
      >
        {t("pagination.previous")}
      </button>
      <span className="text-gray-600 tabular-nums">
        {t("pagination.pageOf", { page, totalPages, total })}
      </span>
      <button
        type="button"
        disabled={disabled || page >= totalPages}
        onClick={() => onPageChange(page + 1)}
        className="rounded-md border border-gray-300 px-3 py-1.5 font-medium text-gray-800 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
      >
        {t("pagination.next")}
      </button>
    </nav>
  );
}
