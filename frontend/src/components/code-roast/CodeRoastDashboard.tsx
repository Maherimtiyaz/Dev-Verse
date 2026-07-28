'use client';

import { useState } from 'react';
import { reviewCode, getReviewStatus } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Loader2, Flame, Shield, Zap, Code, Trophy } from 'lucide-react';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Label } from '@/components/ui/label';

interface CodeReviewResult {
  architecture_review: string;
  security_review: string;
  performance_review: string;
  roast_summary: string;
  overall_score: number;
}

export function CodeRoastDashboard() {
  const [repoUrl, setRepoUrl] = useState('');
  const [mode, setMode] = useState<'professional' | 'roast'>('professional');
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState<CodeReviewResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleReview = async () => {
    if (!repoUrl.trim()) return;
    
    setLoading(true);
    setError(null);
    setResult(null);
    setProgress(0);

    try {
      const response = await reviewCode(repoUrl, mode);
      
      if (response.task_id) {
        const pollInterval = setInterval(async () => {
          const status = await getReviewStatus(response.task_id!);
          setProgress(status.progress || 0);
          
          if (status.status === 'completed' && status.result) {
            setResult(status.result);
            clearInterval(pollInterval);
            setLoading(false);
          } else if (status.status === 'failed') {
            setError('Review failed. Please try again.');
            clearInterval(pollInterval);
            setLoading(false);
          }
        }, 2000);
      } else {
        setResult(response as any);
        setLoading(false);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Review failed');
      setLoading(false);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Flame className="w-6 h-6" />
            AI Code Roast
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="repo-url">Repository URL</Label>
            <Input
              id="repo-url"
              placeholder="https://github.com/username/repo"
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label>Review Mode</Label>
            <RadioGroup value={mode} onValueChange={(v) => setMode(v as any)}>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="professional" id="professional" />
                <Label htmlFor="professional">Professional Feedback</Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="roast" id="roast" />
                <Label htmlFor="roast">Gen-Z Roast Mode 💀</Label>
              </div>
            </RadioGroup>
          </div>

          <Button onClick={handleReview} disabled={loading || !repoUrl.trim()} className="w-full">
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Code className="w-4 h-4" />}
            {mode === 'roast' ? 'Roast My Code' : 'Review Code'}
          </Button>

          {loading && (
            <div className="space-y-2">
              <Progress value={progress} className="w-full" />
              <p className="text-sm text-muted-foreground text-center">
                {mode === 'roast' ? 'Preparing the burns...' : 'Analyzing your code...'} {progress}%
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

      {result && (
        <>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span className="flex items-center gap-2">
                  <Trophy className="w-5 h-5" />
                  Overall Score
                </span>
                <span className={`text-3xl font-bold ${getScoreColor(result.overall_score)}`}>
                  {result.overall_score}/100
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Progress value={result.overall_score} className="w-full" />
            </CardContent>
          </Card>

          <div className="grid md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Code className="w-5 h-5 text-blue-600" />
                  Architecture Review
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                  {result.architecture_review}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="w-5 h-5 text-green-600" />
                  Security Review
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                  {result.security_review}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Zap className="w-5 h-5 text-yellow-600" />
                  Performance Review
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                  {result.performance_review}
                </p>
              </CardContent>
            </Card>

            <Card className={mode === 'roast' ? 'border-orange-500' : ''}>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Flame className="w-5 h-5 text-orange-600" />
                  {mode === 'roast' ? 'The Roast 🔥' : 'Summary'}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm whitespace-pre-wrap">
                  {result.roast_summary}
                </p>
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}
