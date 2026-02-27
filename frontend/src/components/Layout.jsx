import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, 
  LineChart, 
  Newspaper, 
  Globe, 
  GitBranch, 
  Filter, 
  Settings,
  Search,
  Bell,
  TrendingUp
} from 'lucide-react';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';

const Sidebar = () => {
  const location = useLocation();
  
  const navItems = [
    { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
    { path: '/quote', icon: LineChart, label: 'Quote' },
    { path: '/news', icon: Newspaper, label: 'News' },
    { path: '/worldmap', icon: Globe, label: 'World Map' },
    { path: '/supplychain', icon: GitBranch, label: 'Supply Chain' },
    { path: '/screener', icon: Filter, label: 'Screener' },
  ];

  return (
    <aside className="w-56 bg-zinc-950 border-r border-zinc-800 flex flex-col h-screen fixed left-0 top-0">
      {/* Logo */}
      <div className="p-4 border-b border-zinc-800">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-orange-500 rounded-sm flex items-center justify-center">
            <TrendingUp className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-sm font-semibold text-white tracking-tight">NEXUS</h1>
            <p className="text-[10px] text-zinc-500 uppercase tracking-wider">Terminal</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-2 space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path;
          
          return (
            <NavLink
              key={item.path}
              to={item.path}
              data-testid={`nav-${item.label.toLowerCase().replace(' ', '-')}`}
              className={`sidebar-item ${isActive ? 'active' : ''}`}
            >
              <Icon className="w-4 h-4" />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      {/* Bottom section */}
      <div className="p-3 border-t border-zinc-800">
        <NavLink to="/settings" className="sidebar-item">
          <Settings className="w-4 h-4" />
          <span>Settings</span>
        </NavLink>
        <div className="mt-3 px-3">
          <p className="text-[10px] text-zinc-600 uppercase tracking-wider">v1.0.0</p>
        </div>
      </div>
    </aside>
  );
};

const TopBar = ({ onSearch }) => {
  const [searchQuery, setSearchQuery] = React.useState('');

  const handleSearch = (e) => {
    e.preventDefault();
    if (onSearch) onSearch(searchQuery);
  };

  return (
    <header className="h-12 bg-zinc-950 border-b border-zinc-800 flex items-center justify-between px-4 fixed top-0 left-56 right-0 z-50">
      {/* Search */}
      <form onSubmit={handleSearch} className="flex items-center gap-2 flex-1 max-w-md">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
          <Input
            type="text"
            placeholder="Search assets... (e.g., AAPL, Gold, EUR/USD)"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9 bg-zinc-900 border-zinc-800 text-sm h-8"
            data-testid="search-input"
          />
        </div>
      </form>

      {/* Right side */}
      <div className="flex items-center gap-3">
        {/* Live indicator */}
        <div className="live-indicator text-zinc-400">
          <span className="text-emerald-500">LIVE</span>
        </div>

        {/* Time */}
        <div className="font-mono text-xs text-zinc-400">
          {new Date().toLocaleTimeString('en-US', { hour12: false })}
        </div>

        {/* Notifications */}
        <Button variant="ghost" size="sm" className="h-8 w-8 p-0" data-testid="notifications-btn">
          <Bell className="w-4 h-4 text-zinc-400" />
        </Button>
      </div>
    </header>
  );
};

const Layout = ({ children }) => {
  const handleSearch = (query) => {
    // Navigate to quote page with search query
    if (query) {
      window.location.href = `/quote?symbol=${query.toUpperCase()}`;
    }
  };

  return (
    <div className="min-h-screen bg-[#09090b]">
      <Sidebar />
      <TopBar onSearch={handleSearch} />
      <main className="ml-56 pt-12 min-h-screen">
        <div className="p-4">
          {children}
        </div>
      </main>
    </div>
  );
};

export default Layout;
