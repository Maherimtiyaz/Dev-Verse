import { getCookie } from 'cookies-next';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export interface ApiError {
  detail: string;
  status_code?: number;
}

async function fetchWithAuth<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getCookie('access_token');
  
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const error: ApiError = await response.json().catch(() => ({
      detail: 'An unexpected error occurred',
    }));
    throw new Error(error.detail);
  }

  return response.json();
}

// GitHub Twin API
export async function analyzeGithubProfile(username?: string) {
  return fetchWithAuth<{
    dna: {
      skills: string[];
      strengths: string[];
      weaknesses: string[];
      engineering_style: string;
      recommended_learning: string[];
    };
    task_id?: string;
  }>('/agents/github-analyzer/analyze', {
    method: 'POST',
    body: JSON.stringify({ github_username: username }),
  });
}

export async function getAnalysisStatus(taskId: string) {
  return fetchWithAuth<{
    status: 'pending' | 'processing' | 'completed' | 'failed';
    result?: any;
    progress?: number;
  }>(`/agents/github-analyzer/status/${taskId}`);
}

// Code Roast API
export async function reviewCode(
  repoUrl: string,
  mode: 'professional' | 'roast' = 'professional'
) {
  return fetchWithAuth<{
    architecture_review: string;
    security_review: string;
    performance_review: string;
    roast_summary: string;
    overall_score: number;
    task_id?: string;
  }>('/agents/code-review/review', {
    method: 'POST',
    body: JSON.stringify({ repo_url: repoUrl, mode }),
  });
}

export async function getReviewStatus(taskId: string) {
  return fetchWithAuth<{
    status: 'pending' | 'processing' | 'completed' | 'failed';
    result?: any;
    progress?: number;
  }>(`/agents/code-review/status/${taskId}`);
}

// Matchmaker API
export async function matchProjects(filters?: {
  technologies?: string[];
  difficulty?: 'beginner' | 'intermediate' | 'advanced';
  interests?: string[];
}) {
  return fetchWithAuth<{
    matches: Array<{
      project_id: string;
      name: string;
      description: string;
      technologies: string[];
      match_score: number;
      first_issue_suggestion: string;
      contribution_roadmap: string[];
    }>;
  }>('/agents/project-recommendation/match', {
    method: 'POST',
    body: JSON.stringify(filters || {}),
  });
}

// Hackathon Partner API
export async function findPartners(filters?: {
  required_skills?: string[];
  preferred_technologies?: string[];
  availability?: string;
  timezone?: string;
}) {
  return fetchWithAuth<{
    partners: Array<{
      user_id: string;
      username: string;
      skills: string[];
      compatibility_score: number;
      shared_interests: string[];
      complementary_skills: string[];
      availability: string;
    }>;
  }>('/agents/hackathon-partner/match', {
    method: 'POST',
    body: JSON.stringify(filters || {}),
  });
}

// Auth API
export async function loginWithGitHub(code: string, state: string) {
  const response = await fetch(`${API_BASE_URL}/auth/github/callback`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code, state }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Login failed' }));
    throw new Error(error.detail);
  }

  return response.json();
}

export async function getCurrentUser() {
  return fetchWithAuth<{
    id: string;
    email: string;
    username: string;
    profile?: {
      bio?: string;
      avatar_url?: string;
      skills: string[];
    };
  }>('/users/me');
}
