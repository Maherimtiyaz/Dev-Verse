import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { GitHubTwinDashboard } from '@/components/github-twin/GitHubTwinDashboard';
import * as api from '@/lib/api';

// Mock the API module
jest.mock('@/lib/api', () => ({
  analyzeGithubProfile: jest.fn(),
  getAnalysisStatus: jest.fn(),
}));

describe('GitHubTwinDashboard', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders input field and analyze button', () => {
    render(<GitHubTwinDashboard />);
    
    expect(screen.getByPlaceholderText(/github username/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /analyze/i })).toBeInTheDocument();
  });

  it('disables analyze button when input is empty', () => {
    render(<GitHubTwinDashboard />);
    
    const button = screen.getByRole('button', { name: /analyze/i });
    expect(button).toBeDisabled();
  });

  it('enables analyze button when username is entered', async () => {
    render(<GitHubTwinDashboard />);
    
    const input = screen.getByPlaceholderText(/github username/i);
    fireEvent.change(input, { target: { value: 'torvalds' } });
    
    const button = screen.getByRole('button', { name: /analyze/i });
    expect(button).not.toBeDisabled();
  });

  it('calls analyzeGithubProfile API when analyze is clicked', async () => {
    const mockDna = {
      dna: {
        skills: ['Python', 'C'],
        strengths: ['System Design', 'Code Review'],
        weaknesses: ['Documentation'],
        engineering_style: 'Minimalist',
        recommended_learning: ['Rust'],
      },
    };

    (api.analyzeGithubProfile as jest.Mock).mockResolvedValue(mockDna);

    render(<GitHubTwinDashboard />);
    
    const input = screen.getByPlaceholderText(/github username/i);
    fireEvent.change(input, { target: { value: 'torvalds' } });
    
    const button = screen.getByRole('button', { name: /analyze/i });
    fireEvent.click(button);

    await waitFor(() => {
      expect(api.analyzeGithubProfile).toHaveBeenCalledWith('torvalds');
    });
  });

  it('displays DNA results after successful analysis', async () => {
    const mockDna = {
      dna: {
        skills: ['Python', 'C'],
        strengths: ['System Design', 'Code Review'],
        weaknesses: ['Documentation'],
        engineering_style: 'Minimalist',
        recommended_learning: ['Rust'],
      },
    };

    (api.analyzeGithubProfile as jest.Mock).mockResolvedValue(mockDna);

    render(<GitHubTwinDashboard />);
    
    const input = screen.getByPlaceholderText(/github username/i);
    fireEvent.change(input, { target: { value: 'torvalds' } });
    
    const button = screen.getByRole('button', { name: /analyze/i });
    fireEvent.click(button);

    await waitFor(() => {
      expect(screen.getByText(/Minimalist/i)).toBeInTheDocument();
      expect(screen.getByText(/System Design/i)).toBeInTheDocument();
      expect(screen.getByText(/Python/i)).toBeInTheDocument();
    });
  });

  it('displays error message on API failure', async () => {
    (api.analyzeGithubProfile as jest.Mock).mockRejectedValue(new Error('API Error'));

    render(<GitHubTwinDashboard />);
    
    const input = screen.getByPlaceholderText(/github username/i);
    fireEvent.change(input, { target: { value: 'torvalds' } });
    
    const button = screen.getByRole('button', { name: /analyze/i });
    fireEvent.click(button);

    await waitFor(() => {
      expect(screen.getByText(/API Error/i)).toBeInTheDocument();
    });
  });
});
