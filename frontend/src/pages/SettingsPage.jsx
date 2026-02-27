import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Switch } from '../components/ui/switch';
import { 
  Settings as SettingsIcon,
  Bell,
  Globe,
  Palette,
  Clock,
  Shield,
  Download,
  Info
} from 'lucide-react';

const SettingsPage = () => {
  return (
    <div className="max-w-4xl mx-auto space-y-4" data-testid="settings-page">
      {/* Header */}
      <Card className="nexus-card">
        <CardContent className="p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-orange-500/20 rounded-sm flex items-center justify-center">
              <SettingsIcon className="w-5 h-5 text-orange-500" />
            </div>
            <div>
              <h1 className="text-xl font-semibold text-white">Settings</h1>
              <p className="text-sm text-zinc-500">Configure your terminal preferences</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Display Settings */}
      <Card className="nexus-card">
        <CardHeader className="card-header-terminal">
          <CardTitle className="card-header-title flex items-center gap-2">
            <Palette className="w-4 h-4 text-orange-500" />
            Display
          </CardTitle>
        </CardHeader>
        <CardContent className="p-4 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-white">Dark Mode</p>
              <p className="text-xs text-zinc-500">Use dark theme for the terminal</p>
            </div>
            <Switch checked={true} disabled />
          </div>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-white">Compact Mode</p>
              <p className="text-xs text-zinc-500">Reduce padding for more data density</p>
            </div>
            <Switch />
          </div>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-white">Show Mini Charts</p>
              <p className="text-xs text-zinc-500">Display sparkline charts in tables</p>
            </div>
            <Switch defaultChecked />
          </div>
        </CardContent>
      </Card>

      {/* Notifications */}
      <Card className="nexus-card">
        <CardHeader className="card-header-terminal">
          <CardTitle className="card-header-title flex items-center gap-2">
            <Bell className="w-4 h-4 text-orange-500" />
            Notifications
          </CardTitle>
        </CardHeader>
        <CardContent className="p-4 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-white">Price Alerts</p>
              <p className="text-xs text-zinc-500">Get notified when price targets are hit</p>
            </div>
            <Switch defaultChecked />
          </div>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-white">Breaking News</p>
              <p className="text-xs text-zinc-500">Alerts for major market news</p>
            </div>
            <Switch defaultChecked />
          </div>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-white">Geopolitical Alerts</p>
              <p className="text-xs text-zinc-500">High-impact conflict notifications</p>
            </div>
            <Switch defaultChecked />
          </div>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-white">Supply Chain Risks</p>
              <p className="text-xs text-zinc-500">Alerts for supply chain disruptions</p>
            </div>
            <Switch />
          </div>
        </CardContent>
      </Card>

      {/* Data & Updates */}
      <Card className="nexus-card">
        <CardHeader className="card-header-terminal">
          <CardTitle className="card-header-title flex items-center gap-2">
            <Clock className="w-4 h-4 text-orange-500" />
            Data & Updates
          </CardTitle>
        </CardHeader>
        <CardContent className="p-4 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-white">Auto-refresh Interval</p>
              <p className="text-xs text-zinc-500">How often to update market data</p>
            </div>
            <Badge variant="outline" className="rounded-none">60 seconds</Badge>
          </div>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-white">Data Provider</p>
              <p className="text-xs text-zinc-500">Source for market quotes</p>
            </div>
            <Badge variant="outline" className="rounded-none">Yahoo Finance</Badge>
          </div>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-white">News Source</p>
              <p className="text-xs text-zinc-500">Provider for news articles</p>
            </div>
            <Badge variant="outline" className="rounded-none">NewsAPI</Badge>
          </div>
        </CardContent>
      </Card>

      {/* About */}
      <Card className="nexus-card">
        <CardHeader className="card-header-terminal">
          <CardTitle className="card-header-title flex items-center gap-2">
            <Info className="w-4 h-4 text-orange-500" />
            About
          </CardTitle>
        </CardHeader>
        <CardContent className="p-4">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-zinc-400">Version</span>
              <span className="font-mono text-sm text-white">1.0.0</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-zinc-400">Build</span>
              <span className="font-mono text-sm text-white">2026.01.28</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-zinc-400">License</span>
              <span className="text-sm text-white">Professional</span>
            </div>
          </div>
          
          <div className="mt-6 pt-4 border-t border-zinc-800">
            <p className="text-xs text-zinc-500">
              NEXUS Terminal - Professional-grade financial intelligence platform.
              Built with React, FastAPI, and MongoDB.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Export */}
      <Card className="nexus-card">
        <CardHeader className="card-header-terminal">
          <CardTitle className="card-header-title flex items-center gap-2">
            <Download className="w-4 h-4 text-orange-500" />
            Export Data
          </CardTitle>
        </CardHeader>
        <CardContent className="p-4">
          <div className="flex items-center gap-3">
            <Button variant="outline" size="sm">
              Export Watchlist (CSV)
            </Button>
            <Button variant="outline" size="sm">
              Export Settings (JSON)
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default SettingsPage;
