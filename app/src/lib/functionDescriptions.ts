/**
 * Human-readable descriptions for agent function executions.
 * Maps function names to user-friendly descriptions for active state.
 */
export const FUNCTION_DESCRIPTIONS: Record<string, string> = {
  get_inventory_snapshot: "Checking inventory...",
  add_inventory_items: "Adding items to inventory...",
  place_order: "Placing your order...",
  check_low_stock: "Checking for low stock items...",
  get_recent_orders: "Fetching recent orders...",
  update_user_preferences: "Updating your preferences...",
  get_user_info: "Retrieving your information...",
};

/**
 * Human-readable descriptions for completed function executions.
 * Maps function names to user-friendly descriptions for done state.
 */
export const FUNCTION_DESCRIPTIONS_DONE: Record<string, string> = {
  get_inventory_snapshot: "Checked inventory",
  add_inventory_items: "Added items to inventory",
  place_order: "Placed your order",
  check_low_stock: "Checked for low stock items",
  get_recent_orders: "Fetched recent orders",
  update_user_preferences: "Updated your preferences",
  get_user_info: "Retrieved your information",
};

/**
 * Get a human-readable description for a function name.
 * Falls back to a formatted version of the function name if not found.
 * 
 * @param functionName - The function name to get description for
 * @param isDone - Whether the function execution is complete
 */
export function getFunctionDescription(functionName: string, isDone = false): string {
  if (isDone) {
    return (
      FUNCTION_DESCRIPTIONS_DONE[functionName] ||
      functionName
        .split("_")
        .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
        .join(" ")
        .replace(/\b\w/g, (l) => l.toUpperCase())
    );
  }
  
  return (
    FUNCTION_DESCRIPTIONS[functionName] ||
    functionName
      .split("_")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ")
      .replace(/\b\w/g, (l) => l.toUpperCase()) + "..."
  );
}

/**
 * Parse execution messages from stream content.
 * Matches patterns like [Executing function_name...]
 */
export function parseExecutionMessage(content: string): {
  functionName: string | null;
  description: string | null;
} {
  const match = content.match(/\[Executing\s+(\w+)\s*\.\.\.\]/);
  if (match) {
    const functionName = match[1];
    return {
      functionName,
      description: getFunctionDescription(functionName),
    };
  }
  return { functionName: null, description: null };
}
