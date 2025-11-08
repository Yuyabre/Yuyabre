import { useState } from "react";
import { Modal } from "../ui/Modal";
import { useStore } from "../../store/useStore";
import { userApi } from "../../lib/api";
import { IconUsers, IconPlus } from "@tabler/icons-react";

interface GroupModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function GroupModal({ open, onOpenChange }: GroupModalProps) {
  const { currentUser, currentGroup, setCurrentGroup } = useStore();
  const [showAddFlatmate, setShowAddFlatmate] = useState(false);
  const [flatmateEmail, setFlatmateEmail] = useState("");

  const handleAddFlatmate = async () => {
    if (!flatmateEmail.trim() || !currentUser?.isAdmin) return;

    try {
      const updatedGroup = await userApi.addFlatmate(flatmateEmail);
      setCurrentGroup(updatedGroup);
      setFlatmateEmail("");
      setShowAddFlatmate(false);
    } catch (error) {
      console.error("Failed to add flatmate:", error);
    }
  };

  const getInitials = (name: string) => {
    return name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);
  };

  if (!currentGroup) return null;

  return (
    <Modal
      open={open}
      onOpenChange={onOpenChange}
      title={currentGroup.name}
      description="Manage your flat and flatmates"
    >
      <div className="space-y-4">
        <div className="flex items-center gap-2 text-sm text-zinc-600 dark:text-zinc-400">
          <IconUsers className="size-4" />
          <span>{currentGroup.members.length} flatmate{currentGroup.members.length !== 1 ? "s" : ""}</span>
        </div>

        <div className="space-y-2">
          {currentGroup.members.map((member) => (
            <div
              key={member.id}
              className={`flex items-center gap-3 p-3 rounded-lg border ${
                member.id === currentUser?.id
                  ? "bg-zinc-100 dark:bg-zinc-800 border-zinc-200 dark:border-zinc-700"
                  : "border-zinc-200 dark:border-zinc-800"
              }`}
            >
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white font-semibold text-sm flex-shrink-0">
                {member.avatar ? (
                  <img src={member.avatar} alt={member.name} className="w-full h-full rounded-full object-cover" />
                ) : (
                  <span>{getInitials(member.name)}</span>
                )}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-zinc-900 dark:text-zinc-100">
                    {member.name}
                  </span>
                  {member.id === currentUser?.id && (
                    <span className="text-xs text-zinc-500 dark:text-zinc-400">(You)</span>
                  )}
                  {member.isAdmin && (
                    <span className="text-xs px-2 py-0.5 bg-zinc-200 dark:bg-zinc-700 text-zinc-700 dark:text-zinc-300 rounded">
                      Admin
                    </span>
                  )}
                </div>
                <div className="text-sm text-zinc-500 dark:text-zinc-400">{member.email}</div>
              </div>
            </div>
          ))}
        </div>

        {currentUser?.isAdmin && (
          <div className="pt-2 border-t border-zinc-200 dark:border-zinc-800">
            {showAddFlatmate ? (
              <div className="space-y-2">
                <input
                  type="email"
                  placeholder="Email address"
                  value={flatmateEmail}
                  onChange={(e) => setFlatmateEmail(e.target.value)}
                  className="w-full px-3 py-2 border border-zinc-200 dark:border-zinc-800 rounded-md bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 text-sm focus:outline-none focus:ring-2 focus:ring-zinc-400 dark:focus:ring-zinc-600"
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      handleAddFlatmate();
                    } else if (e.key === "Escape") {
                      setShowAddFlatmate(false);
                      setFlatmateEmail("");
                    }
                  }}
                  autoFocus
                />
                <div className="flex gap-2">
                  <button
                    onClick={handleAddFlatmate}
                    className="flex-1 px-3 py-2 bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 rounded-md text-sm font-medium hover:bg-zinc-800 dark:hover:bg-zinc-200 transition-colors"
                  >
                    Add
                  </button>
                  <button
                    onClick={() => {
                      setShowAddFlatmate(false);
                      setFlatmateEmail("");
                    }}
                    className="flex-1 px-3 py-2 border border-zinc-200 dark:border-zinc-800 rounded-md text-sm hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <button
                onClick={() => setShowAddFlatmate(true)}
                className="w-full flex items-center justify-center gap-2 px-3 py-2 border border-dashed border-zinc-300 dark:border-zinc-700 rounded-md text-sm text-zinc-600 dark:text-zinc-400 hover:border-zinc-400 dark:hover:border-zinc-600 hover:text-zinc-900 dark:hover:text-zinc-300 transition-colors"
              >
                <IconPlus className="size-4" />
                <span>Add Flatmate</span>
              </button>
            )}
          </div>
        )}
      </div>
    </Modal>
  );
}

