'use client';

import { useState } from 'react';
import { findPartners } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Loader2, Users, Sparkles, Clock, Globe } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';

interface PartnerMatch {
  user_id: string;
  username: string;
  skills: string[];
  compatibility_score: number;
  shared_interests: string[];
  complementary_skills: string[];
  availability: string;
}

export function HackathonFinderDashboard() {
  const [requiredSkills, setRequiredSkills] = useState('');
  const [preferredTech, setPreferredTech] = useState('');
  const [availability, setAvailability] = useState('');
  const [timezone, setTimezone] = useState('');
  const [loading, setLoading] = useState(false);
  const [partners, setPartners] = useState<PartnerMatch[]>([]);
  const [error, setError] = useState<string | null>(null);

  const handleFindPartners = async () => {
    setLoading(true);
    setError(null);
    setPartners([]);

    try {
      const filters: any = {};
      if (requiredSkills.trim()) {
        filters.required_skills = requiredSkills.split(',').map(s => s.trim()).filter(Boolean);
      }
      if (preferredTech.trim()) {
        filters.preferred_technologies = preferredTech.split(',').map(t => t.trim()).filter(Boolean);
      }
      if (availability.trim()) {
        filters.availability = availability;
      }
      if (timezone.trim()) {
        filters.timezone = timezone;
      }

      const result = await findPartners(filters);
      setPartners(result.partners);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Partner search failed');
    } finally {
      setLoading(false);
    }
  };

  const getCompatibilityColor = (score: number) => {
    if (score >= 85) return 'text-green-600 bg-green-100';
    if (score >= 70) return 'text-yellow-600 bg-yellow-100';
    return 'text-orange-600 bg-orange-100';
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="w-6 h-6" />
            AI Hackathon Partner Finder
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="required-skills">Required Skills (comma-separated)</Label>
              <Input
                id="required-skills"
                placeholder="Backend, Frontend, Design"
                value={requiredSkills}
                onChange={(e) => setRequiredSkills(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="preferred-tech">Preferred Technologies</Label>
              <Input
                id="preferred-tech"
                placeholder="React, Node.js, Python"
                value={preferredTech}
                onChange={(e) => setPreferredTech(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="availability">Availability</Label>
              <Input
                id="availability"
                placeholder="Full-time, Evenings only, Weekends"
                value={availability}
                onChange={(e) => setAvailability(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="timezone">Timezone</Label>
              <Input
                id="timezone"
                placeholder="UTC-5, EST, PST"
                value={timezone}
                onChange={(e) => setTimezone(e.target.value)}
              />
            </div>
          </div>

          <Button onClick={handleFindPartners} disabled={loading} className="w-full">
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
            Find Teammates
          </Button>

          {error && (
            <div className="p-4 bg-destructive/10 text-destructive rounded-lg">
              {error}
            </div>
          )}
        </CardContent>
      </Card>

      {partners.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-xl font-semibold">Potential Teammates ({partners.length})</h3>
          {partners.map((partner, index) => (
            <Card key={partner.user_id} className="border-l-4" style={{ borderLeftColor: partner.compatibility_score >= 85 ? '#22c55e' : partner.compatibility_score >= 70 ? '#eab308' : '#f97316' }}>
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div className="flex items-center gap-3">
                    <Avatar className="h-12 w-12">
                      <AvatarImage src={`https://github.com/${partner.username}.png`} />
                      <AvatarFallback>{partner.username.substring(0, 2).toUpperCase()}</AvatarFallback>
                    </Avatar>
                    <div>
                      <CardTitle>@{partner.username}</CardTitle>
                      <div className="flex items-center gap-2 mt-1">
                        <Badge className={getCompatibilityColor(partner.compatibility_score)}>
                          {partner.compatibility_score}% Compatible
                        </Badge>
                      </div>
                    </div>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <h4 className="font-medium mb-2">Skills</h4>
                  <div className="flex flex-wrap gap-2">
                    {partner.skills.map((skill, i) => (
                      <Badge key={i} variant="outline">
                        {skill}
                      </Badge>
                    ))}
                  </div>
                </div>

                {partner.shared_interests.length > 0 && (
                  <div className="bg-green-50 dark:bg-green-950/20 p-3 rounded-lg">
                    <h4 className="font-medium text-green-900 dark:text-green-100 mb-1 flex items-center gap-2">
                      <Sparkles className="w-4 h-4" />
                      Shared Interests
                    </h4>
                    <div className="flex flex-wrap gap-1">
                      {partner.shared_interests.map((interest, i) => (
                        <Badge key={i} variant="secondary" className="bg-green-200 text-green-800">
                          {interest}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                {partner.complementary_skills.length > 0 && (
                  <div className="bg-blue-50 dark:bg-blue-950/20 p-3 rounded-lg">
                    <h4 className="font-medium text-blue-900 dark:text-blue-100 mb-1">
                      Complementary Skills (Brings what you lack)
                    </h4>
                    <div className="flex flex-wrap gap-1">
                      {partner.complementary_skills.map((skill, i) => (
                        <Badge key={i} variant="secondary" className="bg-blue-200 text-blue-800">
                          {skill}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                <div className="grid grid-cols-2 gap-2">
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Clock className="w-4 h-4" />
                    <span>Availability: {partner.availability}</span>
                  </div>
                  {timezone && (
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Globe className="w-4 h-4" />
                      <span>Timezone compatible</span>
                    </div>
                  )}
                </div>

                <div className="flex gap-2">
                  <Button size="sm" className="flex-1">Invite to Team</Button>
                  <Button size="sm" variant="outline">View Profile</Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {partners.length === 0 && !loading && !error && (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            <Users className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>Enter your team requirements to find compatible hackathon partners.</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
