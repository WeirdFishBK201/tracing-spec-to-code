from __future__ import annotations

from dataclasses import dataclass

from .artifacts import ArtifactRef


CLOSED_PLAN_STATUSES = frozenset({"Completed", "Delivered"})


@dataclass(frozen=True)
class MilestoneLifecycle:
    milestone_sequence: tuple[str, ...]
    active_plans: tuple[ArtifactRef, ...]
    closed_plans: tuple[ArtifactRef, ...]
    closed_milestone_prefix: tuple[str, ...]
    next_milestone_id: str | None
    last_closed_milestone_id: str | None
    last_closed_plan_status: str | None
    earlier_milestones_delivered: bool
    closed_prefix_delivered: bool

    def selected_plan_matches_current(
        self,
        roadmap: ArtifactRef,
        plan: ArtifactRef,
    ) -> bool:
        return plan.milestone_id == roadmap.current_milestone_id

    def active_plan_matches_current(self, roadmap: ArtifactRef) -> bool:
        if len(self.active_plans) != 1:
            return False
        active_plan = self.active_plans[0]
        return (
            active_plan.milestone_id == roadmap.current_milestone_id
            and active_plan.milestone_id == self.next_milestone_id
            and self.closed_prefix_delivered
        )

    def awaiting_current_is_valid(self, roadmap: ArtifactRef) -> bool:
        if roadmap.status != "Awaiting" or self.next_milestone_id is None:
            return False
        if self.last_closed_plan_status == "Completed":
            if not self.earlier_milestones_delivered:
                return False
            expected = self.last_closed_milestone_id
        elif self.last_closed_plan_status == "Delivered":
            if not self.closed_prefix_delivered:
                return False
            expected = self.next_milestone_id
        else:
            return False
        return roadmap.current_milestone_id == expected


def analyze_milestone_lifecycle(
    roadmap: ArtifactRef,
    plans: list[ArtifactRef],
) -> MilestoneLifecycle:
    milestone_sequence: list[str] = []
    for milestone_ref in roadmap.milestone_refs:
        if milestone_ref.milestone_id not in milestone_sequence:
            milestone_sequence.append(milestone_ref.milestone_id)

    active_plans = tuple(
        plan for plan in plans if plan.status not in CLOSED_PLAN_STATUSES
    )
    closed_plans = tuple(
        plan for plan in plans if plan.status in CLOSED_PLAN_STATUSES
    )
    closed_plans_by_id: dict[str | None, list[ArtifactRef]] = {}
    for plan in closed_plans:
        closed_plans_by_id.setdefault(plan.milestone_id, []).append(plan)
    closed_plan_ids = {plan.milestone_id for plan in closed_plans}
    closed_milestone_prefix: list[str] = []
    for milestone_id in milestone_sequence:
        if milestone_id not in closed_plan_ids:
            break
        closed_milestone_prefix.append(milestone_id)

    next_milestone_id = next(
        (
            milestone_id
            for milestone_id in milestone_sequence
            if milestone_id not in closed_milestone_prefix
        ),
        None,
    )
    last_closed_milestone_id = (
        closed_milestone_prefix[-1] if closed_milestone_prefix else None
    )
    last_closed_candidates = closed_plans_by_id.get(
        last_closed_milestone_id,
        [],
    )
    last_closed_plan_status = (
        last_closed_candidates[0].status
        if len(last_closed_candidates) == 1
        else None
    )
    def milestones_are_delivered(milestone_ids: list[str]) -> bool:
        return all(
            len(closed_plans_by_id.get(milestone_id, [])) == 1
            and closed_plans_by_id[milestone_id][0].status == "Delivered"
            for milestone_id in milestone_ids
        )

    earlier_milestones_delivered = milestones_are_delivered(
        closed_milestone_prefix[:-1]
    )
    closed_prefix_delivered = milestones_are_delivered(
        closed_milestone_prefix
    )

    return MilestoneLifecycle(
        milestone_sequence=tuple(milestone_sequence),
        active_plans=active_plans,
        closed_plans=closed_plans,
        closed_milestone_prefix=tuple(closed_milestone_prefix),
        next_milestone_id=next_milestone_id,
        last_closed_milestone_id=last_closed_milestone_id,
        last_closed_plan_status=last_closed_plan_status,
        earlier_milestones_delivered=earlier_milestones_delivered,
        closed_prefix_delivered=closed_prefix_delivered,
    )
