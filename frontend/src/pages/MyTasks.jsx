import { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import api from '../lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Badge } from '../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '../components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Checkbox } from '../components/ui/checkbox';
import { toast } from 'sonner';
import {
  ClipboardList,
  Clock,
  CheckCircle,
  AlertCircle,
  Play,
  Send,
  MessageSquare,
  Timer,
  ListTodo,
  Plus,
  Trash2,
  Filter,
  RefreshCw,
  ChevronDown,
  Calendar
} from 'lucide-react';

const statusConfig = {
  assigned: { label: 'Assigned', color: 'bg-blue-100 text-blue-800', icon: ClipboardList },
  in_progress: { label: 'In Progress', color: 'bg-yellow-100 text-yellow-800', icon: Clock },
  completed: { label: 'Completed', color: 'bg-orange-100 text-orange-800', icon: AlertCircle },
  verified: { label: 'Verified', color: 'bg-green-100 text-green-800', icon: CheckCircle }
};

const priorityConfig = {
  low: { label: 'Low', color: 'bg-slate-100 text-slate-600' },
  medium: { label: 'Medium', color: 'bg-blue-100 text-blue-700' },
  high: { label: 'High', color: 'bg-orange-100 text-orange-700' },
  urgent: { label: 'Urgent', color: 'bg-red-100 text-red-700' }
};

export default function MyTasks() {
  const [searchParams] = useSearchParams();
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedTask, setSelectedTask] = useState(null);
  const [showDetailModal, setShowDetailModal] = useState(false);

  // Filters
  const [statusFilter, setStatusFilter] = useState('all');
  const [priorityFilter, setPriorityFilter] = useState('all');

  // Comment input
  const [newComment, setNewComment] = useState('');
  const [submittingComment, setSubmittingComment] = useState(false);

  // Subtask input
  const [newSubtask, setNewSubtask] = useState('');

  // Time log input
  const [timeLogHours, setTimeLogHours] = useState('');
  const [timeLogDescription, setTimeLogDescription] = useState('');

  useEffect(() => {
    fetchTasks();
  }, [statusFilter, priorityFilter]);

  useEffect(() => {
    // Open task detail if task param is present
    const taskId = searchParams.get('task');
    if (taskId && tasks.length > 0) {
      const task = tasks.find(t => t.id === taskId);
      if (task) {
        openTaskDetail(task);
      }
    }
  }, [searchParams, tasks]);

  const fetchTasks = async () => {
    try {
      setLoading(true);
      const params = { assigned_to_me: true };
      if (statusFilter !== 'all') params.status = statusFilter;
      if (priorityFilter !== 'all') params.priority = priorityFilter;

      const res = await api.get('/portal/tasks', { params });
      setTasks(res.data);
    } catch (error) {
      toast.error('Failed to load tasks');
    } finally {
      setLoading(false);
    }
  };

  const openTaskDetail = async (task) => {
    try {
      const res = await api.get(`/portal/tasks/${task.id}`);
      setSelectedTask(res.data);
      setShowDetailModal(true);
    } catch (error) {
      toast.error('Failed to load task details');
    }
  };

  const handleStartTask = async (taskId) => {
    try {
      await api.post(`/portal/tasks/${taskId}/start`);
      toast.success('Task started!');
      fetchTasks();
      if (selectedTask?.id === taskId) {
        const res = await api.get(`/portal/tasks/${taskId}`);
        setSelectedTask(res.data);
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to start task');
    }
  };

  const handleCompleteTask = async (taskId) => {
    try {
      await api.post(`/portal/tasks/${taskId}/complete`);
      toast.success('Task marked as completed! Awaiting verification.');
      fetchTasks();
      if (selectedTask?.id === taskId) {
        const res = await api.get(`/portal/tasks/${taskId}`);
        setSelectedTask(res.data);
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to complete task');
    }
  };

  const handleAddComment = async () => {
    if (!newComment.trim() || !selectedTask) return;

    try {
      setSubmittingComment(true);
      await api.post(`/portal/tasks/${selectedTask.id}/comments`, { content: newComment });
      toast.success('Comment added');
      setNewComment('');
      // Refresh task details
      const res = await api.get(`/portal/tasks/${selectedTask.id}`);
      setSelectedTask(res.data);
    } catch (error) {
      toast.error('Failed to add comment');
    } finally {
      setSubmittingComment(false);
    }
  };

  const handleAddSubtask = async () => {
    if (!newSubtask.trim() || !selectedTask) return;

    try {
      await api.post(`/portal/tasks/${selectedTask.id}/subtasks`, { title: newSubtask });
      toast.success('Subtask added');
      setNewSubtask('');
      const res = await api.get(`/portal/tasks/${selectedTask.id}`);
      setSelectedTask(res.data);
    } catch (error) {
      toast.error('Failed to add subtask');
    }
  };

  const handleToggleSubtask = async (subtaskId, isCompleted) => {
    if (!selectedTask) return;

    try {
      await api.put(`/portal/tasks/${selectedTask.id}/subtasks/${subtaskId}?is_completed=${!isCompleted}`);
      const res = await api.get(`/portal/tasks/${selectedTask.id}`);
      setSelectedTask(res.data);
    } catch (error) {
      toast.error('Failed to update subtask');
    }
  };

  const handleAddTimeLog = async () => {
    if (!timeLogHours || !selectedTask) return;

    try {
      await api.post(`/portal/tasks/${selectedTask.id}/time-logs`, {
        hours: parseFloat(timeLogHours),
        description: timeLogDescription
      });
      toast.success('Time logged');
      setTimeLogHours('');
      setTimeLogDescription('');
      const res = await api.get(`/portal/tasks/${selectedTask.id}`);
      setSelectedTask(res.data);
    } catch (error) {
      toast.error('Failed to log time');
    }
  };

  // Group tasks by status for Kanban-like view
  const tasksByStatus = {
    assigned: tasks.filter(t => t.status === 'assigned'),
    in_progress: tasks.filter(t => t.status === 'in_progress'),
    completed: tasks.filter(t => t.status === 'completed'),
    verified: tasks.filter(t => t.status === 'verified')
  };

  return (
    <div className="space-y-6" data-testid="my-tasks-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <ClipboardList className="w-6 h-6 text-indigo-600" />
            My Tasks
          </h1>
          <p className="text-slate-500 text-sm mt-1">View and manage your assigned tasks</p>
        </div>
        <Button onClick={fetchTasks} variant="outline" size="sm">
          <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="py-4">
          <div className="flex flex-wrap gap-4 items-center">
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-slate-400" />
              <span className="text-sm font-medium">Filters:</span>
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-40" data-testid="status-filter">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="assigned">Assigned</SelectItem>
                <SelectItem value="in_progress">In Progress</SelectItem>
                <SelectItem value="completed">Completed</SelectItem>
                <SelectItem value="verified">Verified</SelectItem>
              </SelectContent>
            </Select>
            <Select value={priorityFilter} onValueChange={setPriorityFilter}>
              <SelectTrigger className="w-40" data-testid="priority-filter">
                <SelectValue placeholder="Priority" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Priority</SelectItem>
                <SelectItem value="urgent">Urgent</SelectItem>
                <SelectItem value="high">High</SelectItem>
                <SelectItem value="medium">Medium</SelectItem>
                <SelectItem value="low">Low</SelectItem>
              </SelectContent>
            </Select>
            <span className="text-sm text-slate-500 ml-auto">
              {tasks.length} task(s)
            </span>
          </div>
        </CardContent>
      </Card>

      {/* Tasks Board */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <RefreshCw className="w-8 h-8 animate-spin text-indigo-600" />
        </div>
      ) : tasks.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <ClipboardList className="w-12 h-12 mx-auto mb-4 text-slate-300" />
            <p className="text-slate-500">No tasks found</p>
            <p className="text-sm text-slate-400 mt-1">Tasks assigned to you will appear here</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {Object.entries(tasksByStatus).map(([status, statusTasks]) => (
            <div key={status} className="space-y-3">
              <div className="flex items-center gap-2 px-2">
                <div className={`w-3 h-3 rounded-full ${
                  status === 'assigned' ? 'bg-blue-500' :
                  status === 'in_progress' ? 'bg-yellow-500' :
                  status === 'completed' ? 'bg-orange-500' :
                  'bg-green-500'
                }`} />
                <span className="font-medium text-sm capitalize">{status.replace('_', ' ')}</span>
                <Badge variant="secondary" className="ml-auto">{statusTasks.length}</Badge>
              </div>
              <div className="space-y-2 min-h-[200px]">
                {statusTasks.map((task) => (
                  <Card
                    key={task.id}
                    className="cursor-pointer hover:shadow-md transition-shadow"
                    onClick={() => openTaskDetail(task)}
                    data-testid={`task-card-${task.id}`}
                  >
                    <CardContent className="p-3">
                      <div className="flex items-start justify-between mb-2">
                        <p className="font-medium text-sm line-clamp-2">{task.title}</p>
                        {task.priority && (
                          <Badge className={priorityConfig[task.priority]?.color || ''} variant="secondary">
                            {task.priority}
                          </Badge>
                        )}
                      </div>
                      <p className="text-xs text-slate-500 mb-2">{task.task_number}</p>
                      {task.category_name && (
                        <Badge 
                          variant="outline" 
                          className="text-xs mb-2"
                          style={{ borderColor: task.category_color, color: task.category_color }}
                        >
                          {task.category_name}
                        </Badge>
                      )}
                      <div className="flex items-center justify-between text-xs text-slate-400">
                        {task.due_date && (
                          <span className="flex items-center gap-1">
                            <Calendar className="w-3 h-3" />
                            {new Date(task.due_date).toLocaleDateString()}
                          </span>
                        )}
                        {task.subtasks_total > 0 && (
                          <span className="flex items-center gap-1">
                            <ListTodo className="w-3 h-3" />
                            {task.subtasks_completed}/{task.subtasks_total}
                          </span>
                        )}
                        {task.total_hours > 0 && (
                          <span className="flex items-center gap-1">
                            <Timer className="w-3 h-3" />
                            {task.total_hours}h
                          </span>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Task Detail Modal */}
      <Dialog open={showDetailModal} onOpenChange={setShowDetailModal}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          {selectedTask && (
            <>
              <DialogHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <DialogTitle className="text-lg">{selectedTask.title}</DialogTitle>
                    <DialogDescription className="flex items-center gap-2 mt-1">
                      <span>{selectedTask.task_number}</span>
                      {selectedTask.category_name && (
                        <Badge 
                          variant="outline" 
                          style={{ borderColor: selectedTask.category_color, color: selectedTask.category_color }}
                        >
                          {selectedTask.category_name}
                        </Badge>
                      )}
                    </DialogDescription>
                  </div>
                  <Badge className={statusConfig[selectedTask.status]?.color}>
                    {statusConfig[selectedTask.status]?.label}
                  </Badge>
                </div>
              </DialogHeader>

              <Tabs defaultValue="details" className="mt-4">
                <TabsList className="grid w-full grid-cols-4">
                  <TabsTrigger value="details">Details</TabsTrigger>
                  <TabsTrigger value="subtasks">
                    Subtasks ({selectedTask.subtasks?.length || 0})
                  </TabsTrigger>
                  <TabsTrigger value="time">
                    Time ({selectedTask.total_hours || 0}h)
                  </TabsTrigger>
                  <TabsTrigger value="comments">
                    Comments ({selectedTask.comments?.length || 0})
                  </TabsTrigger>
                </TabsList>

                {/* Details Tab */}
                <TabsContent value="details" className="space-y-4 mt-4">
                  {selectedTask.description && (
                    <div>
                      <Label className="text-xs text-slate-500">Description</Label>
                      <p className="text-sm mt-1 whitespace-pre-wrap">{selectedTask.description}</p>
                    </div>
                  )}
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label className="text-xs text-slate-500">Priority</Label>
                      <p className="text-sm mt-1">
                        <Badge className={priorityConfig[selectedTask.priority]?.color}>
                          {selectedTask.priority}
                        </Badge>
                      </p>
                    </div>
                    <div>
                      <Label className="text-xs text-slate-500">Due Date</Label>
                      <p className="text-sm mt-1">
                        {selectedTask.due_date ? new Date(selectedTask.due_date).toLocaleDateString() : 'No due date'}
                      </p>
                    </div>
                    {selectedTask.amount > 0 && (
                      <div>
                        <Label className="text-xs text-slate-500">Payment Amount</Label>
                        <p className="text-sm mt-1 font-medium text-green-600">
                          LKR {selectedTask.amount.toLocaleString()}
                        </p>
                      </div>
                    )}
                  </div>

                  {/* Action Buttons */}
                  <div className="flex gap-2 pt-4 border-t">
                    {selectedTask.status === 'assigned' && (
                      <Button onClick={() => handleStartTask(selectedTask.id)} data-testid="start-task-btn">
                        <Play className="w-4 h-4 mr-2" />
                        Start Task
                      </Button>
                    )}
                    {(selectedTask.status === 'assigned' || selectedTask.status === 'in_progress') && (
                      <Button 
                        onClick={() => handleCompleteTask(selectedTask.id)} 
                        variant="outline"
                        className="text-green-600 border-green-600 hover:bg-green-50"
                        data-testid="complete-task-btn"
                      >
                        <CheckCircle className="w-4 h-4 mr-2" />
                        Mark Complete
                      </Button>
                    )}
                  </div>
                </TabsContent>

                {/* Subtasks Tab */}
                <TabsContent value="subtasks" className="space-y-4 mt-4">
                  <div className="flex gap-2">
                    <Input
                      placeholder="Add a subtask..."
                      value={newSubtask}
                      onChange={(e) => setNewSubtask(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && handleAddSubtask()}
                    />
                    <Button onClick={handleAddSubtask} size="sm">
                      <Plus className="w-4 h-4" />
                    </Button>
                  </div>
                  <div className="space-y-2">
                    {(selectedTask.subtasks || []).map((subtask) => (
                      <div
                        key={subtask.id}
                        className="flex items-center gap-3 p-2 border rounded hover:bg-slate-50"
                      >
                        <Checkbox
                          checked={subtask.is_completed}
                          onCheckedChange={() => handleToggleSubtask(subtask.id, subtask.is_completed)}
                        />
                        <span className={subtask.is_completed ? 'line-through text-slate-400' : ''}>
                          {subtask.title}
                        </span>
                      </div>
                    ))}
                    {(!selectedTask.subtasks || selectedTask.subtasks.length === 0) && (
                      <p className="text-center text-slate-400 py-4">No subtasks yet</p>
                    )}
                  </div>
                </TabsContent>

                {/* Time Tracking Tab */}
                <TabsContent value="time" className="space-y-4 mt-4">
                  <div className="flex gap-2">
                    <Input
                      type="number"
                      placeholder="Hours"
                      value={timeLogHours}
                      onChange={(e) => setTimeLogHours(e.target.value)}
                      className="w-24"
                      step="0.5"
                      min="0"
                    />
                    <Input
                      placeholder="Description (optional)"
                      value={timeLogDescription}
                      onChange={(e) => setTimeLogDescription(e.target.value)}
                      className="flex-1"
                    />
                    <Button onClick={handleAddTimeLog} size="sm">
                      <Plus className="w-4 h-4" />
                    </Button>
                  </div>
                  <div className="space-y-2">
                    {(selectedTask.time_logs || []).map((log) => (
                      <div
                        key={log.id}
                        className="flex items-center justify-between p-2 border rounded"
                      >
                        <div>
                          <span className="font-medium">{log.hours}h</span>
                          {log.description && (
                            <span className="text-slate-500 ml-2">- {log.description}</span>
                          )}
                        </div>
                        <span className="text-xs text-slate-400">{log.log_date}</span>
                      </div>
                    ))}
                    {(!selectedTask.time_logs || selectedTask.time_logs.length === 0) && (
                      <p className="text-center text-slate-400 py-4">No time logged yet</p>
                    )}
                  </div>
                  <div className="pt-2 border-t">
                    <p className="text-sm font-medium">
                      Total: <span className="text-indigo-600">{selectedTask.total_hours || 0} hours</span>
                    </p>
                  </div>
                </TabsContent>

                {/* Comments Tab */}
                <TabsContent value="comments" className="space-y-4 mt-4">
                  <div className="flex gap-2">
                    <Textarea
                      placeholder="Add a comment..."
                      value={newComment}
                      onChange={(e) => setNewComment(e.target.value)}
                      rows={2}
                    />
                    <Button 
                      onClick={handleAddComment} 
                      disabled={submittingComment || !newComment.trim()}
                      size="sm"
                    >
                      <Send className="w-4 h-4" />
                    </Button>
                  </div>
                  <div className="space-y-3 max-h-60 overflow-y-auto">
                    {(selectedTask.comments || []).map((comment) => (
                      <div
                        key={comment.id}
                        className={`p-3 rounded-lg ${comment.is_system ? 'bg-amber-50 border-amber-200' : 'bg-slate-50'}`}
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span className="font-medium text-sm">{comment.user_name}</span>
                          <span className="text-xs text-slate-400">
                            {new Date(comment.created_at).toLocaleString()}
                          </span>
                        </div>
                        <p className="text-sm">{comment.content}</p>
                      </div>
                    ))}
                    {(!selectedTask.comments || selectedTask.comments.length === 0) && (
                      <p className="text-center text-slate-400 py-4">No comments yet</p>
                    )}
                  </div>
                </TabsContent>
              </Tabs>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
