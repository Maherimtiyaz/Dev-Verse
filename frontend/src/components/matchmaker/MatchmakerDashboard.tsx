'use client';

import { useState } from 'react';
import { matchProjects } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Loader2, Github, ExternalLink, Map, Lightbulb } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

interface ProjectMatch {
  project_id: string;
  name: string;
  description: string;
  technologies: string[];
  match_score: number;
  first_issue_suggestion: string;
  contribution_roadmap: string[];
}

export function MatchmakerDashboard() {
  const [technologies, setTechnologies] = useState('');
  const [difficulty, setDifficulty] = useState<'beginner' | 'intermediate' | 'advanced' | ''>('');
  const [interests, setInterests] = useState('');
  const [loading, setLoading] = useState(false);
  const [matches, setMatches] = useState<ProjectMatch[]>([]);
  const [error, setError] = useState<string | null>(null);

  const handleMatch = async () => {
    setLoading(true);
    setError(null);
    setMatches([]);

    try {
      const filters: any = {};
      if (technologies.trim()) {
        filters.technologies = technologies.split(',').map(t => t.trim()).filter(Boolean);
      }
      if (difficulty) {
        filters.difficulty = difficulty;
      }
      if (interests.trim()) {
        filters.interests = interests.split(',').map(i => i.trim()).filter(Boolean);
      }

      const result = await matchProjects(filters);
      setMatches(result.matches);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Matching failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Github className="w-6 h-6" />
            AI Open Source Matchmaker
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label htmlFor="technologies">Technologies (comma-separated)</Label>
              <Input
                id="technologies"
                placeholder="React, Python, PostgreSQL"
                value={technologies}
                onChange={(e) => setTechnologies(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="difficulty">Difficulty Level</Label>
              <select
                id="difficulty"
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                value={difficulty}
                onChange={(e) => setDifficulty(e.target.value as any)}
              >
                <option value="">Any</option>
                <option value="beginner">Beginner</option>
                <option value="intermediate">Intermediate</option>
                <option value="advanced">Advanced</option>
              </select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="interests">Interests (comma-separated)</Label>
              <Input
                id="interests"
                placeholder="AI, Web3, DevTools"
                value={interests}
                onChange={(e) => setInterests(e.target.value)}
              />
            </div>
          </div>

          <Button onClick={handleMatch} disabled={loading} className="w-full">
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Map className="w-4 h-4" />}
            Find Perfect Projects
          </Button>

          {error && (
            <div className="p-4 bg-destructive/10 text-destructive rounded-lg">
              {error}
            </div>
          )}
        </CardContent>
      </Card>

      {matches.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-xl font-semibold">Recommended Projects ({matches.length})</h3>
          {matches.map((project, index) => (
            <Card key={project.project_id} className="border-l-4 border-l-green-500">
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      #{index + 1}: {project.name}
                    </CardTitle>
                    <p className="text-sm text-muted-foreground mt-1">{project.description}</p>
                  </div>
                  <Badge variant={project.match_score >= 80 ? 'default' : 'secondary'}>
                    {project.match_score}% Match
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex flex-wrap gap-2">
                  {project.technologies.map((tech, i) => (
                    <Badge key={i} variant="outline">
                      {tech}
                    </Badge>
                  ))}
                </div>

                <div className="bg-blue-50 dark:bg-blue-950/20 p-4 rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <Lightbulb className="w-4 h-4 text-blue-600" />
                    <h4 className="font-medium text-blue-900 dark:text-blue-100">First Issue Suggestion</h4>
                  </div>
                  <p className="text-sm text-blue-800 dark:text-blue-200">{project.first_issue_suggestion}</p>
                </div>

                <div>
                  <h4 className="font-medium mb-2 flex items-center gap-2">
                    <Map className="w-4 h-4" />
                    Contribution Roadmap
                  </h4>
                  <ol className="list-decimal list-inside space-y-1 text-sm text-muted-foreground">
                    {project.contribution_roadmap.map((step, i) => (
                      <li key={i}>{step}</li>
                    ))}
                  </ol>
                </div>

                <Button variant="outline" size="sm" className="w-full">
                  <ExternalLink className="w-4 h-4 mr-2" />
                  View on GitHub
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {matches.length === 0 && !loading && !error && (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            <Github className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>Enter your preferences to find open source projects that match your skills and interests.</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
