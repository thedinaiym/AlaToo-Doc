import DocumentDetailPage from "@/src/features/documents/DocumentDetailPage";

type Props = {
  params: Promise<{
    id: string;
  }>;
};

export default async function DocumentDetailRoute({ params }: Props) {
  const { id } = await params;

  return <DocumentDetailPage documentId={id} />;
}
