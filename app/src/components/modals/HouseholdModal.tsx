import { useMemo } from "react";
import { toast } from "sonner";
import { Modal } from "../basic/Modal";
import { Separator } from "../ui/separator";
import { useStore } from "@/store/useStore";
import {
  IconUsers,
  IconCopy,
  IconMapPin,
  IconPhone,
  IconNote,
  IconMail,
} from "@tabler/icons-react";
import { useHouseholdMembers } from "@/lib/queries";
import { Avatar, AvatarFallback } from "../ui/avatar";

interface HouseholdModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function HouseholdModal({ open, onOpenChange }: HouseholdModalProps) {
  const { currentHousehold, currentUser } = useStore();

  const memberIds = useMemo(
    () => (open && currentHousehold ? [...currentHousehold.member_ids] : []),
    [open, currentHousehold]
  );

  const {
    members,
    isLoading: membersLoading,
    isError: membersError,
  } = useHouseholdMembers(memberIds);

  const membersById = useMemo(() => {
    return new Map(members.map((member) => [member.user_id, member]));
  }, [members]);

  const orderedMembers = useMemo(() => {
    return memberIds
      .map((id) => membersById.get(id))
      .filter((member): member is (typeof members)[number] => Boolean(member));
  }, [memberIds, membersById]);

  const handleCopyInviteCode = async () => {
    if (!currentHousehold?.invite_code) {
      return;
    }

    try {
      await navigator.clipboard.writeText(currentHousehold.invite_code);
      toast.success("Invite code copied to clipboard!");
    } catch (error) {
      console.error("Failed to copy invite code:", error);
      toast.error("Unable to copy invite code.");
    }
  };

  if (!currentHousehold) {
    return null;
  }

  const hasAddress = currentHousehold.address || currentHousehold.city || currentHousehold.postal_code || currentHousehold.country;
  const hasDiscord = currentHousehold.discord_channel_id;

  const getInitials = (name: string) =>
    name
      .split(" ")
      .map((part) => part.charAt(0))
      .join("")
      .toUpperCase()
      .slice(0, 2);

  return (
    <Modal
      open={open}
      onOpenChange={onOpenChange}
      title="Household"
      description="Manage your household settings and invite code."
    >
      <div className="space-y-4">
        {/* Household Name and Invite Code */}
        <div className="flex items-center gap-3 rounded-lg border border-border bg-muted/40 p-4">
          <IconUsers className="size-5 text-muted-foreground flex-shrink-0" />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-foreground">
              {currentHousehold.name}
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              {currentHousehold.member_ids.length} member{currentHousehold.member_ids.length !== 1 ? "s" : ""}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <div className="text-right">
              <p className="text-xs text-muted-foreground">Invite code</p>
              <p className="text-xs font-mono font-medium text-foreground">
                {currentHousehold.invite_code}
              </p>
            </div>
            <button
              type="button"
              className="inline-flex items-center gap-1.5 rounded-md border border-border px-2.5 py-1.5 text-xs font-medium transition-colors hover:bg-muted"
              onClick={handleCopyInviteCode}
            >
              <IconCopy className="size-3.5" />
              Copy
            </button>
          </div>
        </div>

        <Separator />

        {/* Members */}
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <IconUsers className="size-4 text-muted-foreground" />
            <h3 className="text-sm font-semibold text-foreground">Members</h3>
          </div>

          {membersError && (
            <div className="pl-6 text-sm text-destructive">
              Failed to load members. Please try again later.
            </div>
          )}

          {membersLoading && !membersError && (
            <div className="pl-6 space-y-2">
              {Array.from({ length: Math.max(memberIds.length, 2) }).map(
                (_, index) => (
                  <div
                    key={index}
                    className="flex items-center gap-3 rounded-md border border-border/60 p-3 animate-pulse"
                  >
                    <div className="h-9 w-9 rounded-full bg-muted" />
                    <div className="flex-1 space-y-2">
                      <div className="h-3 w-32 rounded bg-muted" />
                      <div className="h-2.5 w-24 rounded bg-muted/80" />
                    </div>
                  </div>
                )
              )}
            </div>
          )}

          {!membersLoading && !membersError && orderedMembers.length === 0 && (
            <div className="pl-6 text-sm text-muted-foreground">
              No members yet. Share the invite code below to add flatmates.
            </div>
          )}

          {!membersLoading && !membersError && orderedMembers.length > 0 && (
            <div className="pl-1 space-y-2">
              {orderedMembers.map((member) => {
                const isCurrent = member.user_id === currentUser?.user_id;
                return (
                  <div
                    key={member.user_id}
                    className="flex items-center gap-3 rounded-lg border border-border/70 p-3"
                  >
                    <Avatar className="h-10 w-10">
                      <AvatarFallback>{getInitials(member.name)}</AvatarFallback>
                    </Avatar>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-medium text-foreground truncate">
                          {member.name}
                        </p>
                        {isCurrent && (
                          <span className="text-xs rounded-full bg-muted px-2 py-0.5 text-muted-foreground">
                            You
                          </span>
                        )}
                      </div>
                      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground mt-1">
                        {member.email && (
                          <span className="inline-flex items-center gap-1">
                            <IconMail className="size-3.5" />
                            <span className="truncate">{member.email}</span>
                          </span>
                        )}
                        {member.phone && (
                          <span className="inline-flex items-center gap-1">
                            <IconPhone className="size-3.5" />
                            <span className="truncate">{member.phone}</span>
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        <Separator />

        {/* Address Information */}
        {hasAddress && (
          <>
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <IconMapPin className="size-4 text-muted-foreground" />
                <h3 className="text-sm font-semibold text-foreground">Address</h3>
              </div>
              <div className="pl-6 space-y-1 text-sm text-muted-foreground">
                {currentHousehold.address && (
                  <p className="text-foreground">{currentHousehold.address}</p>
                )}
                {(currentHousehold.city || currentHousehold.postal_code || currentHousehold.country) && (
                  <p>
                    {[currentHousehold.city, currentHousehold.postal_code, currentHousehold.country]
                      .filter(Boolean)
                      .join(", ")}
                  </p>
                )}
              </div>
            </div>
            <Separator />
          </>
        )}

        {/* Discord Information */}
        {hasDiscord && (
          <>
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <IconPhone className="size-4 text-muted-foreground" />
                <h3 className="text-sm font-semibold text-foreground">Discord</h3>
              </div>
              <div className="pl-6 space-y-1 text-sm text-muted-foreground">
                {currentHousehold.discord_channel_id && (
                  <p className="font-mono">{currentHousehold.discord_channel_id}</p>
                )}
              </div>
            </div>
            <Separator />
          </>
        )}

        {/* Notes */}
        {currentHousehold.notes && (
          <>
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <IconNote className="size-4 text-muted-foreground" />
                <h3 className="text-sm font-semibold text-foreground">Notes</h3>
              </div>
              <p className="pl-6 text-sm text-muted-foreground">
                {currentHousehold.notes}
              </p>
            </div>
            <Separator />
          </>
        )}

        {/* Invite Code Instructions */}
        <div className="space-y-2 text-sm text-muted-foreground">
          <p>
            Share the invite code with your flatmates so they can join the
            household. As soon as they join, you&apos;ll see their items,
            expenses, and orders here.
          </p>
        </div>
      </div>
    </Modal>
  );
}

