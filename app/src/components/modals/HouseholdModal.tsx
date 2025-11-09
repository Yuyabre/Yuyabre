import { useMemo, useState, useEffect } from "react";
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
  IconWallet,
  IconSearch,
  IconEdit,
  IconCheck,
  IconX,
  IconLoader2,
} from "@tabler/icons-react";
import { useHouseholdMembers, useUpdateHousehold } from "@/lib/queries";
import { splitwiseApi } from "@/lib/api";
import { Avatar, AvatarFallback } from "../ui/avatar";
import type { SplitwiseGroup, UpdateHouseholdRequest } from "@/types/users";

interface HouseholdModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function HouseholdModal({ open, onOpenChange }: HouseholdModalProps) {
  const { currentHousehold, currentUser, setCurrentHousehold } = useStore();
  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState<UpdateHouseholdRequest>({});
  const [splitwiseSearchQuery, setSplitwiseSearchQuery] = useState("");
  const [splitwiseGroups, setSplitwiseGroups] = useState<SplitwiseGroup[]>([]);
  const [isSearchingGroups, setIsSearchingGroups] = useState(false);
  const [selectedGroupId, setSelectedGroupId] = useState<string | null>(null);

  const updateHousehold = useUpdateHousehold();

  const memberIds = useMemo(
    () => (open && currentHousehold ? [...currentHousehold.member_ids] : []),
    [open, currentHousehold]
  );

  const {
    members,
    isLoading: membersLoading,
    isError: membersError,
  } = useHouseholdMembers(memberIds);

  // Initialize edit form when entering edit mode
  useEffect(() => {
    if (isEditing && currentHousehold) {
      setEditForm({
        name: currentHousehold.name,
        splitwise_group_id: currentHousehold.splitwise_group_id || null,
        discord_channel_id: currentHousehold.discord_channel_id || null,
        address: currentHousehold.address || null,
        city: currentHousehold.city || null,
        postal_code: currentHousehold.postal_code || null,
        country: currentHousehold.country || null,
        notes: currentHousehold.notes || null,
      });
      setSelectedGroupId(currentHousehold.splitwise_group_id || null);
    }
  }, [isEditing, currentHousehold]);

  // Reset search when modal closes
  useEffect(() => {
    if (!open) {
      setIsEditing(false);
      setSplitwiseSearchQuery("");
      setSplitwiseGroups([]);
      setSelectedGroupId(null);
    }
  }, [open]);

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

  const handleSearchGroups = async () => {
    if (!currentUser || !splitwiseSearchQuery.trim()) {
      return;
    }

    setIsSearchingGroups(true);
    try {
      const response = await splitwiseApi.searchGroups(
        currentUser.user_id,
        splitwiseSearchQuery.trim()
      );
      setSplitwiseGroups(response.groups || []);
    } catch (error) {
      console.error("Error searching Splitwise groups:", error);
      toast.error(
        error instanceof Error
          ? error.message
          : "Failed to search Splitwise groups. Make sure you're connected to Splitwise."
      );
      setSplitwiseGroups([]);
    } finally {
      setIsSearchingGroups(false);
    }
  };

  const handleSelectGroup = (groupId: string) => {
    setSelectedGroupId(groupId);
    setEditForm((prev) => ({ ...prev, splitwise_group_id: groupId }));
  };

  const handleSave = async () => {
    if (!currentUser || !currentHousehold) {
      return;
    }

    try {
      const updated = await updateHousehold.mutateAsync({
        userId: currentUser.user_id,
        householdId: currentHousehold.household_id,
        data: editForm,
      });

      setCurrentHousehold(updated);
      setIsEditing(false);
      toast.success("Household updated!");
    } catch (error) {
      console.error("Error updating household:", error);
      toast.error(
        error instanceof Error
          ? error.message
          : "Failed to update household. Please try again."
      );
    }
  };

  const handleCancel = () => {
    setIsEditing(false);
    setEditForm({});
    setSelectedGroupId(null);
    setSplitwiseSearchQuery("");
    setSplitwiseGroups([]);
  };

  if (!currentHousehold) {
    return null;
  }

  const hasAddress =
    currentHousehold.address ||
    currentHousehold.city ||
    currentHousehold.postal_code ||
    currentHousehold.country;
  const hasDiscord = currentHousehold.discord_channel_id;
  const hasSplitwise = currentHousehold.splitwise_group_id;

  const getInitials = (name: string) =>
    name
      .split(" ")
      .map((part) => part.charAt(0))
      .join("")
      .toUpperCase()
      .slice(0, 2);

  const selectedGroup = splitwiseGroups.find(
    (g) => g.id === selectedGroupId
  ) || (selectedGroupId ? { id: selectedGroupId, name: "Selected group" } : null);

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
            {isEditing ? (
              <input
                type="text"
                value={editForm.name || ""}
                onChange={(e) =>
                  setEditForm((prev) => ({ ...prev, name: e.target.value }))
                }
                className="w-full rounded-md border border-border bg-background px-2 py-1 text-sm font-medium text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                placeholder="Household name"
              />
            ) : (
              <>
            <p className="text-sm font-medium text-foreground">
              {currentHousehold.name}
            </p>
            <p className="text-xs text-muted-foreground mt-1">
                  {currentHousehold.member_ids.length} member
                  {currentHousehold.member_ids.length !== 1 ? "s" : ""}
            </p>
              </>
            )}
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
            {!isEditing && (
              <button
                type="button"
                className="inline-flex items-center gap-1.5 rounded-md border border-border px-2.5 py-1.5 text-xs font-medium transition-colors hover:bg-muted"
                onClick={() => setIsEditing(true)}
              >
                <IconEdit className="size-3.5" />
                Edit
              </button>
            )}
          </div>
        </div>

        {isEditing && (
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handleSave}
              disabled={updateHousehold.isPending}
              className="flex items-center gap-2 rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-70"
            >
              {updateHousehold.isPending ? (
                <IconLoader2 className="size-3.5 animate-spin" />
              ) : (
                <IconCheck className="size-3.5" />
              )}
              Save
            </button>
            <button
              type="button"
              onClick={handleCancel}
              disabled={updateHousehold.isPending}
              className="flex items-center gap-2 rounded-md border border-border px-3 py-1.5 text-xs font-medium text-foreground transition-colors hover:bg-muted disabled:cursor-not-allowed disabled:opacity-70"
            >
              <IconX className="size-3.5" />
              Cancel
            </button>
          </div>
        )}

        <Separator />

        {/* Splitwise Group Section */}
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <IconWallet className="size-4 text-muted-foreground" />
            <h3 className="text-sm font-semibold text-foreground">
              Splitwise Group
            </h3>
          </div>

          {!isEditing && hasSplitwise && (
            <div className="pl-6">
              <div className="rounded-lg border border-border bg-card p-3">
                <p className="text-sm font-medium text-foreground">
                  {currentHousehold.splitwise_group_id}
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  Expenses will be automatically created in this Splitwise group
                </p>
              </div>
            </div>
          )}

          {isEditing && (
            <div className="pl-6 space-y-3">
              {/* Search Input */}
              <div className="space-y-2">
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={splitwiseSearchQuery}
                    onChange={(e) => setSplitwiseSearchQuery(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        handleSearchGroups();
                      }
                    }}
                    placeholder="Search for Splitwise groups..."
                    className="flex-1 rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                  />
                  <button
                    type="button"
                    onClick={handleSearchGroups}
                    disabled={isSearchingGroups || !splitwiseSearchQuery.trim()}
                    className="inline-flex items-center gap-2 rounded-md border border-border bg-background px-3 py-2 text-sm font-medium text-foreground transition-colors hover:bg-muted disabled:cursor-not-allowed disabled:opacity-70"
                  >
                    {isSearchingGroups ? (
                      <IconLoader2 className="size-4 animate-spin" />
                    ) : (
                      <IconSearch className="size-4" />
                    )}
                    Search
                  </button>
                </div>
              </div>

              {/* Search Results */}
              {splitwiseGroups.length > 0 && (
                <div className="space-y-2">
                  <p className="text-xs font-medium text-muted-foreground">
                    Select a group:
                  </p>
                  <div className="space-y-1.5 max-h-48 overflow-y-auto">
                    {splitwiseGroups.map((group) => (
                      <button
                        key={group.id}
                        type="button"
                        onClick={() => handleSelectGroup(group.id)}
                        className={`w-full rounded-md border p-3 text-left transition-colors ${
                          selectedGroupId === group.id
                            ? "border-primary bg-primary/10"
                            : "border-border bg-card hover:bg-muted/50"
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-sm font-medium text-foreground">
                              {group.name}
                            </p>
                            {group.members && group.members.length > 0 && (
                              <p className="text-xs text-muted-foreground mt-1">
                                {group.members.length} member
                                {group.members.length !== 1 ? "s" : ""}
                              </p>
                            )}
                          </div>
                          {selectedGroupId === group.id && (
                            <IconCheck className="size-4 text-primary" />
                          )}
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Selected Group Display */}
              {selectedGroup && (
                <div className="rounded-lg border border-primary bg-primary/10 p-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-foreground">
                        {selectedGroup.name}
                      </p>
                      <p className="text-xs text-muted-foreground mt-1">
                        Selected group
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() => {
                        setSelectedGroupId(null);
                        setEditForm((prev) => ({
                          ...prev,
                          splitwise_group_id: null,
                        }));
                      }}
                      className="text-xs text-muted-foreground hover:text-foreground"
                    >
                      Clear
                    </button>
                  </div>
                </div>
              )}

              {!hasSplitwise && !selectedGroup && (
                <p className="text-xs text-muted-foreground">
                  No Splitwise group selected. Search and select a group to
                  automatically create expenses.
                </p>
              )}
            </div>
          )}
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
                <h3 className="text-sm font-semibold text-foreground">
                  Address
                </h3>
              </div>
              <div className="pl-6 space-y-1 text-sm text-muted-foreground">
                {currentHousehold.address && (
                  <p className="text-foreground">
                    {currentHousehold.address}
                  </p>
                )}
                {(currentHousehold.city ||
                  currentHousehold.postal_code ||
                  currentHousehold.country) && (
                  <p>
                    {[
                      currentHousehold.city,
                      currentHousehold.postal_code,
                      currentHousehold.country,
                    ]
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
                <h3 className="text-sm font-semibold text-foreground">
                  Discord
                </h3>
              </div>
              <div className="pl-6 space-y-1 text-sm text-muted-foreground">
                {currentHousehold.discord_channel_id && (
                  <p className="font-mono">
                    {currentHousehold.discord_channel_id}
                  </p>
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
