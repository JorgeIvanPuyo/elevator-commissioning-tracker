import { ElevatorDetailClient } from "@/features/elevators/ElevatorDetailClient";

export default async function ElevatorDetailPage({ params }: { params: Promise<{ elevatorId: string }> }) {
  const { elevatorId } = await params;
  return <ElevatorDetailClient elevatorId={elevatorId} />;
}
