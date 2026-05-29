import { CommissioningOverviewClient } from "@/features/elevators/CommissioningOverviewClient";

export default async function ElevatorCommissioningOverviewPage({ params }: { params: Promise<{ elevatorId: string }> }) {
  const { elevatorId } = await params;
  return <CommissioningOverviewClient elevatorId={elevatorId} />;
}
