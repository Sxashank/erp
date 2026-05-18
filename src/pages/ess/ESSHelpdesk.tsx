/**
 * ESS Helpdesk Page
 * Raise and track support tickets
 */

import {
  Plus,
  HelpCircle,
  Loader2,
  MessageSquare,
  Clock,
  CheckCircle,
  AlertCircle,
  Send,
  Star,
  RefreshCw,
} from 'lucide-react';
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

import { DateDisplay } from '@/components/common/DateDisplay';
import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import { essHelpdeskApi } from '@/services/essApi';
import { useEssAuthStore } from '@/stores/essAuthStore';
import type { HelpdeskTicket, HelpdeskCategory, TicketSummary, TicketStatus, TicketPriority } from '@/types/ess';

import { logger } from "@/lib/logger";
export default function ESSHelpdeskPage() {
  const navigate = useNavigate();
  const accessToken = useEssAuthStore((state) => state.accessToken);
  const [loading, setLoading] = useState(true);
  const [tickets, setTickets] = useState<HelpdeskTicket[]>([]);
  const [categories, setCategories] = useState<HelpdeskCategory[]>([]);
  const [summary, setSummary] = useState<TicketSummary | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [selectedTicket, setSelectedTicket] = useState<HelpdeskTicket | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [newComment, setNewComment] = useState('');
  const [feedbackRating, setFeedbackRating] = useState(0);

  useEffect(() => {
    if (!accessToken) {
      navigate('/ess/login');
      return;
    }
    fetchData();
  }, [accessToken, navigate, statusFilter]);

  const fetchData = async () => {
    try {
      const [ticketsRes, categoriesRes, summaryRes] = await Promise.all([
        essHelpdeskApi.getTickets({ status: statusFilter !== 'ALL' ? statusFilter : undefined }),
        essHelpdeskApi.getCategories(),
        essHelpdeskApi.getSummary(),
      ]);
      setTickets(ticketsRes.data?.items || []);
      setCategories(categoriesRes.data || []);
      setSummary(summaryRes.data);
    } catch (error) {
      logger.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTicket = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);

    setSubmitting(true);
    try {
      await essHelpdeskApi.createTicket({
        subject: formData.get('subject') as string,
        description: formData.get('description') as string,
        category_type: formData.get('category_type') as string,
        priority: formData.get('priority') as string || 'NORMAL',
      });
      setCreateDialogOpen(false);
      fetchData();
    } catch (error) {
      logger.error('Failed to create ticket:', error);
    } finally {
      setSubmitting(false);
    }
  };

  const handleAddComment = async () => {
    if (!selectedTicket || !newComment.trim()) return;

    setSubmitting(true);
    try {
      await essHelpdeskApi.addComment(selectedTicket.id, { comment: newComment });
      setNewComment('');
      // Refresh ticket details
      const response = await essHelpdeskApi.getTicket(selectedTicket.id);
      setSelectedTicket(response.data);
    } catch (error) {
      logger.error('Failed to add comment:', error);
    } finally {
      setSubmitting(false);
    }
  };

  const handleCloseTicket = async () => {
    if (!selectedTicket) return;
    try {
      await essHelpdeskApi.closeTicket(selectedTicket.id);
      setSelectedTicket(null);
      fetchData();
    } catch (error) {
      logger.error('Failed to close ticket:', error);
    }
  };

  const handleReopenTicket = async () => {
    if (!selectedTicket) return;
    const reason = prompt('Please provide a reason for reopening:');
    if (!reason) return;

    try {
      await essHelpdeskApi.reopenTicket(selectedTicket.id, reason);
      fetchData();
      const response = await essHelpdeskApi.getTicket(selectedTicket.id);
      setSelectedTicket(response.data);
    } catch (error) {
      logger.error('Failed to reopen ticket:', error);
    }
  };

  const handleSubmitFeedback = async () => {
    if (!selectedTicket || feedbackRating === 0) return;

    try {
      await essHelpdeskApi.submitFeedback(selectedTicket.id, {
        rating: feedbackRating,
        feedback: '',
      });
      fetchData();
      setSelectedTicket(null);
    } catch (error) {
      logger.error('Failed to submit feedback:', error);
    }
  };

  const getStatusBadge = (status: TicketStatus) => {
    const styles: Record<TicketStatus, { bg: string; icon: typeof Clock }> = {
      OPEN: { bg: 'bg-blue-100 text-blue-700', icon: Clock },
      IN_PROGRESS: { bg: 'bg-yellow-100 text-yellow-700', icon: Clock },
      PENDING_INFO: { bg: 'bg-orange-100 text-orange-700', icon: AlertCircle },
      RESOLVED: { bg: 'bg-green-100 text-green-700', icon: CheckCircle },
      CLOSED: { bg: 'bg-gray-100 text-gray-700', icon: CheckCircle },
      REOPENED: { bg: 'bg-purple-100 text-purple-700', icon: RefreshCw },
    };
    const style = styles[status];
    const Icon = style.icon;
    return (
      <Badge className={style.bg}>
        <Icon className="h-3 w-3 mr-1" />
        {status.replace('_', ' ')}
      </Badge>
    );
  };

  const getPriorityBadge = (priority: TicketPriority) => {
    const styles: Record<TicketPriority, string> = {
      LOW: 'bg-gray-100 text-gray-600',
      NORMAL: 'bg-blue-100 text-blue-600',
      HIGH: 'bg-orange-100 text-orange-600',
      URGENT: 'bg-red-100 text-red-600',
    };
    return <Badge variant="outline" className={styles[priority]}>{priority}</Badge>;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  const createTicketDialog = (
    <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
      <DialogTrigger asChild>
        <Button>
          <Plus className="h-4 w-4 mr-2" />
          New Ticket
        </Button>
      </DialogTrigger>
          <DialogContent className="max-w-lg">
            <DialogHeader>
              <DialogTitle>Create Support Ticket</DialogTitle>
              <DialogDescription>
                Describe your issue and we'll help you resolve it
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleCreateTicket} className="space-y-4">
              <div>
                <Label htmlFor="category_type">Category</Label>
                <Select name="category_type" required>
                  <SelectTrigger>
                    <SelectValue placeholder="Select category" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="HR">HR Queries</SelectItem>
                    <SelectItem value="IT">IT Support</SelectItem>
                    <SelectItem value="ADMIN">Admin/Facilities</SelectItem>
                    <SelectItem value="FINANCE">Finance</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label htmlFor="priority">Priority</Label>
                <Select name="priority" defaultValue="NORMAL">
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="LOW">Low</SelectItem>
                    <SelectItem value="NORMAL">Normal</SelectItem>
                    <SelectItem value="HIGH">High</SelectItem>
                    <SelectItem value="URGENT">Urgent</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label htmlFor="subject">Subject</Label>
                <Input id="subject" name="subject" placeholder="Brief description of the issue" required />
              </div>
              <div>
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  name="description"
                  placeholder="Provide detailed information about your issue"
                  rows={4}
                  required
                />
              </div>
              <div className="flex gap-3 justify-end">
                <Button type="button" variant="outline" onClick={() => setCreateDialogOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={submitting}>
                  {submitting && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                  Submit Ticket
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title="Helpdesk"
        subtitle="Raise and track your support tickets"
        actions={createTicketDialog}
      />

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold">{summary?.total || 0}</p>
            <p className="text-sm text-gray-500">Total</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-blue-600">{summary?.open || 0}</p>
            <p className="text-sm text-gray-500">Open</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-yellow-600">{summary?.in_progress || 0}</p>
            <p className="text-sm text-gray-500">In Progress</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-green-600">{summary?.resolved || 0}</p>
            <p className="text-sm text-gray-500">Resolved</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-gray-600">{summary?.closed || 0}</p>
            <p className="text-sm text-gray-500">Closed</p>
          </CardContent>
        </Card>
      </div>

      {/* Tickets List */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-base">My Tickets</CardTitle>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-40">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="ALL">All Status</SelectItem>
                <SelectItem value="OPEN">Open</SelectItem>
                <SelectItem value="IN_PROGRESS">In Progress</SelectItem>
                <SelectItem value="RESOLVED">Resolved</SelectItem>
                <SelectItem value="CLOSED">Closed</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
        <CardContent>
          {tickets.length > 0 ? (
            <div className="space-y-4">
              {tickets.map((ticket) => (
                <div
                  key={ticket.id}
                  className="p-4 border rounded-lg hover:bg-gray-50 cursor-pointer"
                  onClick={async () => {
                    const response = await essHelpdeskApi.getTicket(ticket.id);
                    setSelectedTicket(response.data);
                  }}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-medium">{ticket.ticket_number}</span>
                        {getStatusBadge(ticket.status)}
                        {getPriorityBadge(ticket.priority)}
                        {ticket.response_sla_breached && (
                          <Badge variant="destructive" className="text-xs">SLA Breached</Badge>
                        )}
                      </div>
                      <h4 className="font-medium">{ticket.subject}</h4>
                      <p className="text-sm text-gray-500">
                        {ticket.category_type} • Created <DateDisplay date={ticket.created_at} />
                      </p>
                    </div>
                    <MessageSquare className="h-5 w-5 text-gray-400" />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <HelpCircle className="h-8 w-8 mx-auto mb-2 opacity-50" />
              <p>No tickets found</p>
              <Button variant="link" onClick={() => setCreateDialogOpen(true)}>
                Create your first ticket
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Ticket Detail Dialog */}
      <Dialog open={!!selectedTicket} onOpenChange={() => setSelectedTicket(null)}>
        <DialogContent className="max-w-2xl max-h-[90vh]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              {selectedTicket?.ticket_number}
              {selectedTicket && getStatusBadge(selectedTicket.status)}
            </DialogTitle>
          </DialogHeader>
          {selectedTicket && (
            <div className="space-y-4">
              <div>
                <h3 className="font-medium text-lg">{selectedTicket.subject}</h3>
                <p className="text-sm text-gray-500">
                  {selectedTicket.category_type} • {selectedTicket.priority} Priority
                </p>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-sm">{selectedTicket.description}</p>
              </div>

              {/* Comments */}
              <div>
                <p className="font-medium mb-2">Conversation</p>
                <ScrollArea className="h-48 border rounded-lg p-3">
                  {selectedTicket.comments && selectedTicket.comments.length > 0 ? (
                    <div className="space-y-3">
                      {selectedTicket.comments.map((comment) => (
                        <div
                          key={comment.id}
                          className={`p-3 rounded-lg ${
                            comment.author_type === 'EMPLOYEE' ? 'bg-blue-50 ml-8' : 'bg-gray-50 mr-8'
                          }`}
                        >
                          <p className="text-xs text-gray-500 mb-1">
                            {comment.author_type === 'EMPLOYEE' ? 'You' : 'Support'} •{' '}
                            {new Date(comment.created_at).toLocaleString()}
                          </p>
                          <p className="text-sm">{comment.comment}</p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-center text-gray-500 py-4">No comments yet</p>
                  )}
                </ScrollArea>
              </div>

              {/* Add Comment */}
              {['OPEN', 'IN_PROGRESS', 'PENDING_INFO'].includes(selectedTicket.status) && (
                <div className="flex gap-2">
                  <Input
                    placeholder="Type your message..."
                    value={newComment}
                    onChange={(e) => setNewComment(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleAddComment()}
                  />
                  <Button onClick={handleAddComment} disabled={submitting || !newComment.trim()}>
                    <Send className="h-4 w-4" />
                  </Button>
                </div>
              )}

              {/* Actions */}
              <div className="flex gap-2 justify-end pt-4 border-t">
                {selectedTicket.status === 'RESOLVED' && !selectedTicket.rating && (
                  <div className="flex items-center gap-2 mr-auto">
                    <span className="text-sm">Rate:</span>
                    {[1, 2, 3, 4, 5].map((star) => (
                      <Star
                        key={star}
                        className={`h-5 w-5 cursor-pointer ${
                          star <= feedbackRating ? 'fill-yellow-400 text-yellow-400' : 'text-gray-300'
                        }`}
                        onClick={() => setFeedbackRating(star)}
                      />
                    ))}
                    <Button size="sm" onClick={handleSubmitFeedback} disabled={feedbackRating === 0}>
                      Submit
                    </Button>
                  </div>
                )}
                {selectedTicket.status === 'RESOLVED' && (
                  <Button variant="outline" onClick={handleCloseTicket}>
                    Close Ticket
                  </Button>
                )}
                {['RESOLVED', 'CLOSED'].includes(selectedTicket.status) && (
                  <Button variant="outline" onClick={handleReopenTicket}>
                    <RefreshCw className="h-4 w-4 mr-2" />
                    Reopen
                  </Button>
                )}
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
