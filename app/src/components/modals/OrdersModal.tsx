import { useState, useEffect } from "react";
import { Modal } from "../basic/Modal";
import { Separator } from "../ui/separator";
import { useStore } from "@/store/useStore";
import { ordersApi } from "@/lib/api";
import type { Order, OrderStatus } from "@/types/orders";
import {
  IconLoader2,
  IconX,
  IconCheck,
  IconClock,
  IconTruck,
  IconPackage,
  IconAlertCircle,
  IconShoppingCart,
  IconCalendar,
  IconMapPin,
  IconUsers,
} from "@tabler/icons-react";
import { toast } from "sonner";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

interface OrdersModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const getStatusConfig = (status: OrderStatus) => {
  switch (status) {
    case "pending":
      return {
        label: "Pending",
        icon: IconClock,
        color: "text-yellow-500",
        bgColor: "bg-yellow-500/10",
        borderColor: "border-yellow-500/20",
      };
    case "confirmed":
      return {
        label: "Confirmed",
        icon: IconCheck,
        color: "text-blue-500",
        bgColor: "bg-blue-500/10",
        borderColor: "border-blue-500/20",
      };
    case "processing":
      return {
        label: "Processing",
        icon: IconPackage,
        color: "text-purple-500",
        bgColor: "bg-purple-500/10",
        borderColor: "border-purple-500/20",
      };
    case "out_for_delivery":
      return {
        label: "Out for Delivery",
        icon: IconTruck,
        color: "text-orange-500",
        bgColor: "bg-orange-500/10",
        borderColor: "border-orange-500/20",
      };
    case "delivered":
      return {
        label: "Delivered",
        icon: IconCheck,
        color: "text-green-500",
        bgColor: "bg-green-500/10",
        borderColor: "border-green-500/20",
      };
    case "cancelled":
      return {
        label: "Cancelled",
        icon: IconX,
        color: "text-gray-500",
        bgColor: "bg-gray-500/10",
        borderColor: "border-gray-500/20",
      };
    case "failed":
      return {
        label: "Failed",
        icon: IconAlertCircle,
        color: "text-red-500",
        bgColor: "bg-red-500/10",
        borderColor: "border-red-500/20",
      };
    default:
      return {
        label: status,
        icon: IconClock,
        color: "text-muted-foreground",
        bgColor: "bg-muted/10",
        borderColor: "border-border",
      };
  }
};

const formatDate = (dateString: string | null): string => {
  if (!dateString) return "N/A";
  try {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    }).format(date);
  } catch {
    return dateString;
  }
};

const formatCurrency = (amount: number): string => {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "EUR",
  }).format(amount);
};

export function OrdersModal({ open, onOpenChange }: OrdersModalProps) {
  const { currentUser } = useStore();
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const queryClient = useQueryClient();

  const {
    data: orders,
    isLoading,
    isError,
    refetch,
  } = useQuery({
    queryKey: ["orders", currentUser?.user_id],
    queryFn: () => {
      if (currentUser?.user_id) {
        return ordersApi.getUserOrders(currentUser.user_id);
      }
      return ordersApi.getAll();
    },
    enabled: open && !!currentUser,
  });

  const cancelOrderMutation = useMutation({
    mutationFn: (orderId: string) => ordersApi.cancel(orderId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["orders"] });
      toast.success("Order cancelled successfully");
      setSelectedOrder(null);
    },
    onError: (error: Error) => {
      toast.error(error.message || "Failed to cancel order");
    },
  });

  useEffect(() => {
    if (!open) {
      setSelectedOrder(null);
    }
  }, [open]);

  const canCancel = (order: Order): boolean => {
    return (
      order.status === "pending" ||
      order.status === "confirmed" ||
      order.status === "processing"
    );
  };

  if (selectedOrder) {
    const statusConfig = getStatusConfig(selectedOrder.status);
    const StatusIcon = statusConfig.icon;

    return (
      <Modal
        open={open}
        onOpenChange={onOpenChange}
        title="Order Details"
        description={`Order #${selectedOrder.order_id.slice(-8)}`}
      >
        <div className="space-y-4">
          {/* Order Header */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div
                className={`flex items-center gap-2 rounded-lg border px-3 py-1.5 ${statusConfig.bgColor} ${statusConfig.borderColor}`}
              >
                <StatusIcon className={`size-4 ${statusConfig.color}`} />
                <span className={`text-sm font-medium ${statusConfig.color}`}>
                  {statusConfig.label}
                </span>
              </div>
              {selectedOrder.is_group_order && (
                <div className="flex items-center gap-1 rounded-lg border border-border bg-muted/50 px-2 py-1">
                  <IconUsers className="size-3.5 text-muted-foreground" />
                  <span className="text-xs text-muted-foreground">
                    Group Order
                  </span>
                </div>
              )}
            </div>
            {canCancel(selectedOrder) && (
              <button
                onClick={() => {
                  if (
                    confirm(
                      "Are you sure you want to cancel this order? This action cannot be undone."
                    )
                  ) {
                    cancelOrderMutation.mutate(selectedOrder.order_id);
                  }
                }}
                disabled={cancelOrderMutation.isPending}
                className="inline-flex items-center gap-2 rounded-md border border-destructive/50 bg-destructive/10 px-3 py-1.5 text-sm font-medium text-destructive transition-colors hover:bg-destructive/20 disabled:cursor-not-allowed disabled:opacity-70"
              >
                {cancelOrderMutation.isPending ? (
                  <IconLoader2 className="size-4 animate-spin" />
                ) : (
                  <IconX className="size-4" />
                )}
                Cancel Order
              </button>
            )}
          </div>

          <Separator />

          {/* Order Info */}
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <IconCalendar className="size-4" />
              <span>Placed: {formatDate(selectedOrder.timestamp)}</span>
            </div>
            {selectedOrder.delivery_time && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <IconTruck className="size-4" />
                <span>
                  Delivery: {formatDate(selectedOrder.delivery_time)}
                </span>
              </div>
            )}
            {selectedOrder.delivery_address && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <IconMapPin className="size-4" />
                <span>{selectedOrder.delivery_address}</span>
              </div>
            )}
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <IconShoppingCart className="size-4" />
              <span>Service: {selectedOrder.service}</span>
            </div>
            {selectedOrder.external_order_id && (
              <div className="text-xs text-muted-foreground">
                External ID: {selectedOrder.external_order_id}
              </div>
            )}
          </div>

          <Separator />

          {/* Order Items */}
          <div className="space-y-2">
            <h3 className="text-sm font-semibold text-foreground">Items</h3>
            <div className="space-y-2">
              {selectedOrder.items.map((item, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between rounded-lg border border-border bg-card p-3"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-foreground">
                        {item.name}
                      </span>
                      {item.requested_by && item.requested_by.length > 0 && (
                        <span className="text-xs text-muted-foreground">
                          ({item.requested_by.length} requester
                          {item.requested_by.length !== 1 ? "s" : ""})
                        </span>
                      )}
                    </div>
                    <div className="mt-1 flex items-center gap-2 text-xs text-muted-foreground">
                      <span>
                        {item.quantity} {item.unit}
                      </span>
                      <span>•</span>
                      <span>{formatCurrency(item.price)} each</span>
                    </div>
                  </div>
                  <div className="text-sm font-medium text-foreground">
                    {formatCurrency(item.total_price)}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <Separator />

          {/* Order Summary */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Subtotal</span>
              <span className="text-foreground">
                {formatCurrency(selectedOrder.subtotal)}
              </span>
            </div>
            {selectedOrder.delivery_fee > 0 && (
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Delivery Fee</span>
                <span className="text-foreground">
                  {formatCurrency(selectedOrder.delivery_fee)}
                </span>
              </div>
            )}
            <Separator />
            <div className="flex items-center justify-between text-base font-semibold">
              <span className="text-foreground">Total</span>
              <span className="text-foreground">
                {formatCurrency(selectedOrder.total)}
              </span>
            </div>
          </div>

          {selectedOrder.notes && (
            <>
              <Separator />
              <div className="space-y-2">
                <h3 className="text-sm font-semibold text-foreground">Notes</h3>
                <p className="text-sm text-muted-foreground">
                  {selectedOrder.notes}
                </p>
              </div>
            </>
          )}

          {selectedOrder.splitwise_expense_id && (
            <>
              <Separator />
              <div className="text-xs text-muted-foreground">
                Splitwise Expense ID: {selectedOrder.splitwise_expense_id}
              </div>
            </>
          )}

          <div className="pt-2">
            <button
              onClick={() => setSelectedOrder(null)}
              className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm font-medium text-foreground transition-colors hover:bg-muted"
            >
              Back to Orders
            </button>
          </div>
        </div>
      </Modal>
    );
  }

  return (
    <Modal open={open} onOpenChange={onOpenChange} title="Orders">
      <div className="space-y-4">
        {isLoading && (
          <div className="flex items-center justify-center py-8">
            <IconLoader2 className="size-6 animate-spin text-muted-foreground" />
          </div>
        )}

        {isError && (
          <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-center">
            <p className="text-sm text-destructive">
              Failed to load orders. Please try again.
            </p>
            <button
              onClick={() => refetch()}
              className="mt-2 text-sm text-destructive underline"
            >
              Retry
            </button>
          </div>
        )}

        {!isLoading && !isError && (!orders || orders.length === 0) && (
          <div className="py-8 text-center text-muted-foreground">
            <IconShoppingCart className="mx-auto mb-2 size-8 opacity-50" />
            <p>No orders yet</p>
            <p className="mt-1 text-xs">
              Your order history will appear here once you place an order.
            </p>
          </div>
        )}

        {!isLoading && !isError && orders && orders.length > 0 && (
          <div className="space-y-2">
            {orders.map((order) => {
              const statusConfig = getStatusConfig(order.status);
              const StatusIcon = statusConfig.icon;

              return (
                <button
                  key={order.order_id}
                  onClick={() => setSelectedOrder(order)}
                  className="w-full rounded-lg border border-border bg-card p-4 text-left transition-colors hover:bg-muted/50"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 space-y-2">
                      <div className="flex items-center gap-2">
                        <div
                          className={`flex items-center gap-1.5 rounded-md border px-2 py-0.5 ${statusConfig.bgColor} ${statusConfig.borderColor}`}
                        >
                          <StatusIcon
                            className={`size-3.5 ${statusConfig.color}`}
                          />
                          <span
                            className={`text-xs font-medium ${statusConfig.color}`}
                          >
                            {statusConfig.label}
                          </span>
                        </div>
                        {order.is_group_order && (
                          <div className="flex items-center gap-1 rounded-md border border-border bg-muted/50 px-1.5 py-0.5">
                            <IconUsers className="size-3 text-muted-foreground" />
                            <span className="text-xs text-muted-foreground">
                              Group
                            </span>
                          </div>
                        )}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        {formatDate(order.timestamp)}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {order.items.length} item
                        {order.items.length !== 1 ? "s" : ""} •{" "}
                        {formatCurrency(order.total)}
                      </div>
                    </div>
                    <div className="ml-4 text-right">
                      <div className="text-lg font-semibold text-foreground">
                        {formatCurrency(order.total)}
                      </div>
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        )}
      </div>
    </Modal>
  );
}
