import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import {
  ClipboardList,
  Clock,
  Calendar,
  CheckCircle,
  AlertCircle,
  Play,
  ChevronRight,
  User,
  Building2,
  Timer,
  CalendarDays
} from 'lucide-react';

const statusColors = {
  assigned: 'bg-blue-100 text-blue-800',
  in_progress: 'bg-yellow-100 text-yellow-800',
  completed: 'bg-orange-100 text-orange-800',
  verified: 'bg-green-100 text-green-800'
};

const priorityColors = {
  low: 'bg-slate-100 text-slate-600',
  medium: 'bg-blue-100 text-blue-700',
  high: 'bg-orange-100 text-orange-700',
  urgent: 'bg-red-100 text-red-700'
};

export default function MyDashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [dashboardData, setDashboardData] = useState(null);

  useEffect(() => {
    fetchDashboard();
  }, []);

  const fetchDashboard = async () => {
    try {
      setLoading(false);
      const res = await api.get('/portal/my-dashboard');
      setDashboardData(res.data);
    } catch (error) {
      console.error('Failed to load dashboard:', error);
      toast.error('Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  // If no employee record, show message
  if (!dashboardData?.employee) {
    return (
      <div className="space-y-6" data-testid="my-dashboard-page">
        <div className="flex items-center gap-3">
          <User className="w-8 h-8 text-indigo-600" />
          <div>
            <h1 className="text-2xl font-bold text-slate-900">My Dashboard</h1>
            <p className="text-slate-500">Welcome, {user?.full_name}</p>
          </div>
        </div>

        <Card className="border-amber-200 bg-amber-50">
          <CardContent className="py-6">
            <div className="flex items-center gap-3 text-amber-700">
              <AlertCircle className="w-6 h-6" />
              <div>
                <p className="font-medium">Employee Profile Not Found</p>
                <p className="text-sm mt-1">
                  Your user account is not linked to an employee record. Please contact your administrator to set up your employee profile.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  const { employee, tasks, attendance, leave, recent_tasks } = dashboardData;

  return (
    <div className="space-y-6" data-testid="my-dashboard-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-full bg-indigo-100 flex items-center justify-center">
            <User className="w-6 h-6 text-indigo-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900">{employee.name}</h1>
            <div className="flex items-center gap-2 text-sm text-slate-500">
              <span>{employee.designation || 'Employee'}</span>
              {employee.department && (
                <>
                  <span>•</span>
                  <span className="flex items-center gap-1">
                    <Building2 className="w-3 h-3" />
                    {employee.department}
                  </span>
                </>
              )}
            </div>
          </div>
        </div>
        <Button onClick={() => navigate('/my-tasks')} data-testid="view-all-tasks-btn">
          <ClipboardList className="w-4 h-4 mr-2" />
          View All Tasks
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Tasks Overview */}
        <Card className="border-l-4 border-l-indigo-500">
          <CardContent className="py-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">My Tasks</p>
                <p className="text-2xl font-bold text-indigo-600">{tasks.total}</p>
              </div>
              <ClipboardList className="w-8 h-8 text-indigo-200" />
            </div>
            <div className="mt-3 flex flex-wrap gap-2 text-xs">
              <span className="px-2 py-1 bg-blue-50 text-blue-700 rounded">
                {tasks.assigned} Assigned
              </span>
              <span className="px-2 py-1 bg-yellow-50 text-yellow-700 rounded">
                {tasks.in_progress} In Progress
              </span>
            </div>
          </CardContent>
        </Card>

        {/* Pending Verification */}
        <Card className="border-l-4 border-l-orange-500">
          <CardContent className="py-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Pending Verification</p>
                <p className="text-2xl font-bold text-orange-600">{tasks.completed}</p>
              </div>
              <Clock className="w-8 h-8 text-orange-200" />
            </div>
            <p className="mt-3 text-xs text-slate-500">
              Awaiting manager approval
            </p>
          </CardContent>
        </Card>

        {/* Attendance Today */}
        <Card className="border-l-4 border-l-green-500">
          <CardContent className="py-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Today's Attendance</p>
                <p className="text-2xl font-bold text-green-600">
                  {attendance.present_today ? 'Present' : 'Not Marked'}
                </p>
              </div>
              <Calendar className="w-8 h-8 text-green-200" />
            </div>
            <p className="mt-3 text-xs text-slate-500">
              {attendance.clock_in_time ? `Clocked in: ${attendance.clock_in_time}` : 'This month: ' + attendance.this_month + ' days'}
            </p>
          </CardContent>
        </Card>

        {/* Leave Balance */}
        <Card className="border-l-4 border-l-purple-500">
          <CardContent className="py-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Leave Balance</p>
                <p className="text-2xl font-bold text-purple-600">{leave.balance} days</p>
              </div>
              <CalendarDays className="w-8 h-8 text-purple-200" />
            </div>
            {leave.pending > 0 && (
              <p className="mt-3 text-xs text-amber-600">
                {leave.pending} request(s) pending
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Recent Tasks */}
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg">Recent Tasks</CardTitle>
              <CardDescription>Your latest assigned tasks</CardDescription>
            </div>
            <Button variant="ghost" size="sm" onClick={() => navigate('/my-tasks')}>
              View All <ChevronRight className="w-4 h-4 ml-1" />
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {recent_tasks.length === 0 ? (
            <div className="text-center py-8 text-slate-500">
              <ClipboardList className="w-10 h-10 mx-auto mb-2 text-slate-300" />
              <p>No tasks assigned yet</p>
            </div>
          ) : (
            <div className="space-y-3">
              {recent_tasks.map((task) => (
                <div
                  key={task.id}
                  className="flex items-center justify-between p-3 border rounded-lg hover:bg-slate-50 cursor-pointer transition-colors"
                  onClick={() => navigate(`/my-tasks?task=${task.id}`)}
                  data-testid={`task-${task.id}`}
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-2 h-2 rounded-full ${
                      task.status === 'assigned' ? 'bg-blue-500' :
                      task.status === 'in_progress' ? 'bg-yellow-500' :
                      task.status === 'completed' ? 'bg-orange-500' :
                      'bg-green-500'
                    }`} />
                    <div>
                      <p className="font-medium text-sm">{task.title}</p>
                      <p className="text-xs text-slate-500">{task.task_number}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {task.priority && (
                      <Badge className={priorityColors[task.priority] || 'bg-slate-100'}>
                        {task.priority}
                      </Badge>
                    )}
                    <Badge className={statusColors[task.status] || 'bg-slate-100'}>
                      {task.status.replace('_', ' ')}
                    </Badge>
                    {task.due_date && (
                      <span className="text-xs text-slate-400">
                        Due: {new Date(task.due_date).toLocaleDateString()}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="hover:shadow-md transition-shadow cursor-pointer" onClick={() => navigate('/my-tasks')}>
          <CardContent className="py-6 flex items-center gap-4">
            <div className="w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center">
              <ClipboardList className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <p className="font-medium">My Tasks</p>
              <p className="text-sm text-slate-500">View and manage your tasks</p>
            </div>
          </CardContent>
        </Card>

        <Card className="hover:shadow-md transition-shadow cursor-pointer" onClick={() => navigate('/attendance')}>
          <CardContent className="py-6 flex items-center gap-4">
            <div className="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center">
              <Timer className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <p className="font-medium">Attendance</p>
              <p className="text-sm text-slate-500">Clock in/out & history</p>
            </div>
          </CardContent>
        </Card>

        <Card className="hover:shadow-md transition-shadow cursor-pointer" onClick={() => navigate('/leave-management')}>
          <CardContent className="py-6 flex items-center gap-4">
            <div className="w-12 h-12 rounded-full bg-purple-100 flex items-center justify-center">
              <CalendarDays className="w-6 h-6 text-purple-600" />
            </div>
            <div>
              <p className="font-medium">Leave Requests</p>
              <p className="text-sm text-slate-500">Apply for leave</p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
