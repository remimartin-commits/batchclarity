import { Outlet, NavLink, useNavigate } from "react-router-dom";
import { useAuthStore } from "@/stores/authStore";
import { authApi } from "@/lib/api";
import ToastContainer from "@/components/core/Toast";
import clsx from "clsx";

type NavItem = { label: string; path: string; icon: string };

const navGroups: { group: string; items: NavItem[] }[] = [
  {
    group: "Overview",
    items: [
      {
        label: "Dashboard",
        path: "/",
        icon: "M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6",
      },
    ],
  },
  {
    group: "Quality Management",
    items: [
      {
        label: "CAPAs",
        path: "/qms/capas",
        icon: "M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4",
      },
      {
        label: "Deviations",
        path: "/qms/deviations",
        icon: "M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z",
      },
      {
        label: "Change Controls",
        path: "/qms/change-controls",
        icon: "M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4",
      },
    ],
  },
  {
    group: "Manufacturing",
    items: [
      {
        label: "Batch Records",
        path: "/mes/batch-records",
        icon: "M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10",
      },
    ],
  },
  {
    group: "Equipment",
    items: [
      {
        label: "Equipment",
        path: "/equipment",
        icon: "M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M15 12a3 3 0 11-6 0 3 3 0 016 0z",
      },
    ],
  },
  {
    group: "Laboratory",
    items: [
      {
        label: "LIMS — Samples",
        path: "/lims/samples",
        icon: "M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z",
      },
      {
        label: "Env. Monitoring",
        path: "/env-monitoring",
        icon: "M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z",
      },
    ],
  },
  {
    group: "People & Documents",
    items: [
      {
        label: "Training",
        path: "/training",
        icon: "M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253",
      },
      {
        label: "Documents",
        path: "/documents",
        icon: "M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z",
      },
      {
        label: "Security",
        path: "/security",
        icon: "M12 2l7 4v6c0 5-3.5 9.74-7 10-3.5-.26-7-5-7-10V6l7-4zm0 7a2 2 0 100 4 2 2 0 000-4z",
      },
    ],
  },
  {
    group: "Administration",
    items: [
      {
        label: "Admin Users",
        path: "/admin/users",
        icon: "M17 20h5V4H2v16h5m10 0v-2a4 4 0 00-4-4H9a4 4 0 00-4 4v2m12 0H7m8-14a3 3 0 11-6 0 3 3 0 016 0z",
      },
      {
        label: "Admin Roles",
        path: "/admin/roles",
        icon: "M9.75 3a3 3 0 00-3 3v1.5h10.5V6a3 3 0 00-3-3h-4.5zM4.5 9h15A1.5 1.5 0 0121 10.5V18a3 3 0 01-3 3H6a3 3 0 01-3-3v-7.5A1.5 1.5 0 014.5 9z",
      },
    ],
  },
];

export default function Layout() {
  const { user, logout, hasPermission } = useAuthStore();
  const navigate = useNavigate();

  const filteredNavGroups = navGroups
    .map((group) => ({
      ...group,
      items: group.items.filter((item) => {
        if (item.path === "/admin/users") return hasPermission("admin.users.manage");
        if (item.path === "/admin/roles") return hasPermission("admin.roles.manage");
        return true;
      }),
    }))
    .filter((group) => group.items.length > 0);

  async function handleLogout() {
    try {
      await authApi.logout();
    } catch {
      /* ignore */
    }
    logout();
    navigate("/login");
  }

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className="w-64 bg-gray-900 flex flex-col overflow-y-auto flex-shrink-0">
        {/* Logo */}
        <div className="px-6 py-5 border-b border-gray-700 flex-shrink-0">
          <span className="text-white font-bold text-lg tracking-tight">GMP Platform</span>
          <span className="block text-gray-400 text-xs mt-0.5">v0.2.0 — GMP Validated</span>
        </div>

        {/* Nav groups */}
        <nav className="flex-1 px-3 py-4 space-y-6">
          {filteredNavGroups.map((group) => (
            <div key={group.group}>
              <p className="px-3 mb-1 text-gray-500 text-xs font-semibold uppercase tracking-wider">
                {group.group}
              </p>
              <div className="space-y-0.5">
                {group.items.map((item) => (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    end={item.path === "/"}
                    className={({ isActive }) =>
                      clsx(
                        "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                        isActive
                          ? "bg-brand-600 text-white"
                          : "text-gray-400 hover:bg-gray-800 hover:text-white"
                      )
                    }
                  >
                    <svg
                      className="w-4 h-4 flex-shrink-0"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      strokeWidth={1.5}
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" d={item.icon} />
                    </svg>
                    {item.label}
                  </NavLink>
                ))}
              </div>
            </div>
          ))}
        </nav>

        {/* User footer */}
        <div className="px-4 py-4 border-t border-gray-700 flex-shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-brand-600 flex items-center justify-center text-white text-sm font-bold flex-shrink-0">
              {user?.full_name?.[0] ?? "U"}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-white text-sm font-medium truncate">{user?.full_name}</p>
              <p className="text-gray-400 text-xs truncate">{user?.username}</p>
            </div>
            <button
              onClick={handleLogout}
              title="Sign out"
              className="text-gray-400 hover:text-white flex-shrink-0"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
                />
              </svg>
            </button>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>

      {/* Global toast notifications */}
      <ToastContainer />
    </div>
  );
}
