'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { GitHubTwinDashboard } from '@/components/github-twin/GitHubTwinDashboard';
import { CodeRoastDashboard } from '@/components/code-roast/CodeRoastDashboard';
import { MatchmakerDashboard } from '@/components/matchmaker/MatchmakerDashboard';
import { HackathonFinderDashboard } from '@/components/hackathon/HackathonFinderDashboard';
import { Button } from '@/components/ui/button';
import { GitGraph, Flame, Github, Users, LogOut, Sparkles } from 'lucide-react';

export default function Dashboard() {
  const pathname = usePathname();
  const [activeTab, setActiveTab] = useState('github-twin');

  const navItems = [
    { id: 'github-twin', label: 'GitHub Twin', icon: GitGraph },
    { id: 'code-roast', label: 'Code Roast', icon: Flame },
    { id: 'matchmaker', label: 'OSS Matchmaker', icon: Github },
    { id: 'hackathon', label: 'Partner Finder', icon: Users },
  ];

  const renderContent = () => {
    switch (activeTab) {
      case 'github-twin':
        return <GitHubTwinDashboard />;
      case 'code-roast':
        return <CodeRoastDashboard />;
      case 'matchmaker':
        return <MatchmakerDashboard />;
      case 'hackathon':
        return <HackathonFinderDashboard />;
      default:
        return <GitHubTwinDashboard />;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background to-muted">
      {/* Header */}
      <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50">
        <div className="container mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="w-8 h-8 text-primary" />
            <h1 className="text-xl font-bold">DevVerse AI</h1>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="hidden md:flex items-center gap-2 text-sm text-muted-foreground">
              <span>Logged in as</span>
              <span className="font-medium text-foreground">@developer</span>
            </div>
            <Button variant="ghost" size="sm">
              <LogOut className="w-4 h-4 mr-2" />
              Logout
            </Button>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        <div className="grid md:grid-cols-[250px_1fr] gap-8">
          {/* Sidebar Navigation */}
          <aside className="space-y-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <Button
                  key={item.id}
                  variant={activeTab === item.id ? 'default' : 'ghost'}
                  className="w-full justify-start"
                  onClick={() => setActiveTab(item.id)}
                >
                  <Icon className="w-4 h-4 mr-3" />
                  {item.label}
                </Button>
              );
            })}

            <div className="pt-8 mt-8 border-t">
              <div className="p-4 bg-muted rounded-lg">
                <h3 className="font-semibold mb-2">Pro Tip 💡</h3>
                <p className="text-sm text-muted-foreground">
                  Use GitHub Twin to analyze your coding style before hackathons!
                </p>
              </div>
            </div>
          </aside>

          {/* Main Content */}
          <main className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-3xl font-bold tracking-tight">
                  {navItems.find(i => i.id === activeTab)?.label}
                </h2>
                <p className="text-muted-foreground">
                  {activeTab === 'github-twin' && "Discover your developer DNA with AI analysis"}
                  {activeTab === 'code-roast' && "Get brutal honesty or professional feedback on your code"}
                  {activeTab === 'matchmaker' && "Find open source projects that match your skills"}
                  {activeTab === 'hackathon' && "Build your dream hackathon team"}
                </p>
              </div>
            </div>

            {renderContent()}
          </main>
        </div>
      </div>
    </div>
  );
}
