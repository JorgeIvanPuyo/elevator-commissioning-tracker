import { TestRunDetailClient } from "@/features/test-runs/TestRunDetailClient";

export default async function TestRunDetailPage({ params }: { params: Promise<{ testRunId: string }> }) {
  const { testRunId } = await params;
  return <TestRunDetailClient testRunId={testRunId} />;
}
