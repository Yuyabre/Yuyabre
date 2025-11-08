# Yuyabre React App

A React application for shared flat grocery management, built with Vite, Radix UI, Zustand, and TanStack Query.

## Tech Stack

- **React 19** - UI library
- **Vite** - Build tool and dev server
- **Radix UI** - Accessible component primitives (Dialog, Select, Toast)
- **Zustand** - Lightweight state management
- **TanStack Query** - Server state management and data fetching
- **pnpm** - Package manager

## Features

### 🗂️ Inventory Management
- View all inventory items with quantities and expiration dates
- Low stock alerts and warnings
- Expiration date tracking
- Category-based organization

### 🛒 Order Placement
- Select items from inventory to order
- Streaming order placement (inspired by Vercel AI SDK RSC GenUI)
- Real-time progress updates during order processing
- Automatic inventory and expense updates

### 💰 Expense Tracking
- View all Splitwise expenses
- Track pending and settled expenses
- See your share of each expense
- Link expenses to orders

## Getting Started

### Install Dependencies

```bash
cd app
pnpm install
```

### Development

```bash
pnpm dev
```

The app will be available at `http://localhost:5173`

### Build

```bash
pnpm build
```

### Preview Production Build

```bash
pnpm preview
```

## Project Structure

```
app/
├── src/
│   ├── components/          # React components
│   │   ├── InventoryList.jsx    # Inventory display component
│   │   ├── OrderPlacement.jsx   # Order placement with streaming
│   │   └── ExpenseTracking.jsx  # Expense tracking component
│   ├── lib/                 # Utilities and API
│   │   ├── api.js              # Mock API functions
│   │   └── queries.js          # TanStack Query hooks
│   ├── providers/           # Context providers
│   │   └── QueryProvider.jsx   # TanStack Query provider
│   ├── store/              # Zustand stores
│   │   └── useStore.js        # Global state store
│   ├── App.jsx             # Main app component
│   ├── main.jsx            # Entry point
│   └── index.css           # Global styles
├── package.json
└── vite.config.js
```

## Mock API

All API calls are currently mocked using TanStack Query. The mock API includes:

- **Inventory API**: CRUD operations for inventory items
- **Orders API**: Create and track orders
- **Expenses API**: Track Splitwise expenses

To replace with real API calls, update the functions in `src/lib/api.js` to make actual HTTP requests.

## Streaming Order Placement

The order placement feature uses a generator function to simulate streaming updates, similar to the Vercel AI SDK's `streamUI` pattern. This provides real-time feedback during the order process:

1. Processing order
2. Searching for products
3. Adding items to cart
4. Placing order with Thuisbezorgd
5. Updating inventory
6. Creating Splitwise expense

## Development Notes

- All API calls are mocked with simulated delays
- TanStack Query DevTools are available in development
- The UI is responsive and supports light/dark mode
- Components use Radix UI for accessibility

## Next Steps

To connect to real APIs:

1. Replace mock functions in `src/lib/api.js` with actual HTTP calls
2. Update environment variables for API endpoints
3. Add authentication if needed
4. Implement error handling for network failures

## References

- [Vercel AI SDK RSC GenUI Example](https://github.com/vercel-labs/ai-sdk-preview-rsc-genui) - Inspiration for streaming UI patterns
- [TanStack Query Docs](https://tanstack.com/query/latest) - Data fetching and caching
- [Radix UI Docs](https://www.radix-ui.com/) - Component primitives
- [Zustand Docs](https://github.com/pmndrs/zustand) - State management
