'use client';

import { useState } from 'react';
import { analyzeGithubProfile, getAnalysisStatus } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Loader2, GitGraph, Zap, Brain, TrendingUp } from 'lucide-react';

interface DeveloperDNA {
  skills: string[];
  strengths: string[];
  weaknesses: string[];
  engineering_style: string;
  recommended_learning: string[];
}

export function GitHubTwinDashboard() {
  const [username, setUsername] = useState('');
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [dna, setDna] = useState<DeveloperDNA | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async () => {
    if (!username.trim()) return;
    
    setLoading(true);
    setError(null);
    setDna(null);
    setProgress(0);

    try {
      const result = await analyzeGithubProfile(username);
      
      if (result.task_id) {
        // Poll for status
        const pollInterval = setInterval(async () => {
          const status = await getAnalysisStatus(result.task_id!);
          setProgress(status.progress || 0);
          
          if (status.status === 'completed' && status.result) {
            setDna(status.result.dna);
            clearInterval(pollInterval);
            setLoading(false);
          } else if (status.status === 'failed') {
            setError('Analysis failed. Please try again.');
            clearInterval(pollInterval);
            setLoading(false);
          }
        }, 2000);
      } else if (result.dna) {
        setDna(result.dna);
        setLoading(false);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed');
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <GitGraph className="w-6 h-6" />
            AI GitHub Twin
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <Input
              placeholder="Enter GitHub username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleAnalyze()}
            />
            <Button onClick={handleAnalyze} disabled={loading || !username.trim()}>
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
              Analyze
            </Button>
          </div>

          {loading && (
            <div className="space-y-2">
              <Progress value={progress} className="w-full" />
              <p className="text-sm text-muted-foreground text-center">
                Analyzing your developer DNA... {progress}%
              </p>
            </div>
          )}

          {error && (
            <div className="p-4 bg-destructive/10 text-destructive rounded-lg">
              {error}
            </div>
          )}
        </CardContent>
      </Card>

      {dna && (
        <>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Brain className="w-5 h-5" />
                Engineering Style
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-lg font-medium">{dna.engineering_style}</p>
            </CardContent>
          </Card>

          <div className="grid md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-green-600" />
                  Strengths
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {dna.strengths.map((strength, i) => (
                    <Badge key={i} variant="secondary" className="bg-green-100 text-green-800">
                      {strength}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-orange-600 rotate-180" />
                  Areas to Improve
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {dna.weaknesses.map((weakness, i) => (
                    <Badge key={i} variant="secondary" className="bg-orange-100 text-orange-800">
                      {weakness}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Core Skills</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {dna.skills.map((skill, i) => (
                  <Badge key={i} variant="outline">
                    {skill}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-blue-600" />
                Recommended Learning Path
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ol className="list-decimal list-inside space-y-2">
                {dna.recommended_learning.map((item, i) => (
                  <li key={i} className="text-muted-foreground">{item}</li>
                ))}
              </ol>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
