import { useState, useEffect } from 'react';
import api from '../../lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Textarea } from '../../components/ui/textarea';
import { Badge } from '../../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '../../components/ui/dialog';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '../../components/ui/alert-dialog';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table';
import { toast } from 'sonner';
import { 
  Briefcase, 
  Plus, 
  Pencil, 
  Trash2, 
  RefreshCw,
  Shield,
  Building2,
  Users,
  ChevronUp,
  ChevronDown
} from 'lucide-react';

const roleColors = {
  admin: 'bg-red-100 text-red-700',
  manager: 'bg-purple-100 text-purple-700',
  accountant: 'bg-blue-100 text-blue-700',
  store: 'bg-green-100 text-green-700',
  employee: 'bg-slate-100 text-slate-700'
};

const roleLabels = {
  admin: 'Admin',
  manager: 'Manager',
  accountant: 'Accountant',
  store: 'Store Keeper',
  employee: 'Employee'
};

export default function Designations() {
  const [designations, setDesignations] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showDialog, setShowDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [editingDesignation, setEditingDesignation] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);

  const [formData, setFormData] = useState({
    name: '',
    department_id: 'all',
    role: 'employee',
    description: '',
    level: 1
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [desigRes, deptRes] = await Promise.all([
        api.get('/payroll/designations?include_inactive=true'),
        api.get('/payroll/departments')
      ]);
      setDesignations(desigRes.data);
      setDepartments(deptRes.data);
    } catch (error) {
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      department_id: 'all',
      role: 'employee',
      description: '',
      level: 1
    });
    setEditingDesignation(null);
  };

  const handleOpenDialog = (designation = null) => {
    if (designation) {
      setEditingDesignation(designation);
      setFormData({
        name: designation.name,
        department_id: designation.department_id || 'all',
        role: designation.role || 'employee',
        description: designation.description || '',
        level: designation.level || 1
      });
    } else {
      resetForm();
    }
    setShowDialog(true);
  };

  const handleSubmit = async () => {
    if (!formData.name.trim()) {
      toast.error('Designation name is required');
      return;
    }

    try {
      const payload = {
        ...formData,
        department_id: formData.department_id === 'all' ? null : formData.department_id
      };

      if (editingDesignation) {
        await api.put(`/payroll/designations/${editingDesignation.id}`, payload);
        toast.success('Designation updated');
      } else {
        await api.post('/payroll/designations', payload);
        toast.success('Designation created');
      }
      setShowDialog(false);
      resetForm();
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save designation');
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;

    try {
      await api.delete(`/payroll/designations/${deleteTarget.id}`);
      toast.success('Designation deleted');
      setShowDeleteDialog(false);
      setDeleteTarget(null);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete designation');
    }
  };

  const handleToggleActive = async (designation) => {
    try {
      await api.put(`/payroll/designations/${designation.id}`, {
        is_active: !designation.is_active
      });
      toast.success(designation.is_active ? 'Designation deactivated' : 'Designation activated');
      fetchData();
    } catch (error) {
      toast.error('Failed to update designation');
    }
  };

  return (
    <div className="space-y-6" data-testid="designations-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <Briefcase className="w-6 h-6 text-indigo-600" />
            Designations
          </h1>
          <p className="text-slate-500 text-sm mt-1">
            Manage job titles and their permissions
          </p>
        </div>
        <div className="flex gap-2">
          <Button onClick={fetchData} variant="outline" size="sm">
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button onClick={() => handleOpenDialog()} data-testid="add-designation-btn">
            <Plus className="w-4 h-4 mr-2" />
            Add Designation
          </Button>
        </div>
      </div>

      {/* Info Card */}
      <Card className="border-indigo-200 bg-indigo-50">
        <CardContent className="py-4">
          <div className="flex items-start gap-3">
            <Shield className="w-5 h-5 text-indigo-600 mt-0.5" />
            <div className="text-sm text-indigo-800">
              <p className="font-medium">Designation-based Permissions</p>
              <p className="mt-1">Each designation has a role that determines system access:</p>
              <div className="flex flex-wrap gap-2 mt-2">
                {Object.entries(roleLabels).map(([role, label]) => (
                  <Badge key={role} className={roleColors[role]}>{label}</Badge>
                ))}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Designations Table */}
      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <RefreshCw className="w-8 h-8 animate-spin text-indigo-600" />
            </div>
          ) : designations.length === 0 ? (
            <div className="text-center py-12">
              <Briefcase className="w-12 h-12 mx-auto mb-4 text-slate-300" />
              <p className="text-slate-500">No designations created yet</p>
              <Button onClick={() => handleOpenDialog()} className="mt-4">
                <Plus className="w-4 h-4 mr-2" />
                Create First Designation
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Level</TableHead>
                  <TableHead>Designation</TableHead>
                  <TableHead>Department</TableHead>
                  <TableHead>Role/Permission</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {designations.map((designation) => (
                  <TableRow key={designation.id} className={!designation.is_active ? 'opacity-50' : ''}>
                    <TableCell>
                      <div className="flex items-center gap-1">
                        {[...Array(Math.min(designation.level || 1, 5))].map((_, i) => (
                          <ChevronUp key={i} className="w-3 h-3 text-indigo-500" />
                        ))}
                        <span className="text-xs text-slate-500 ml-1">L{designation.level || 1}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div>
                        <p className="font-medium">{designation.name}</p>
                        {designation.description && (
                          <p className="text-xs text-slate-500 truncate max-w-[200px]">{designation.description}</p>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1">
                        <Building2 className="w-3 h-3 text-slate-400" />
                        <span className="text-sm">{designation.department_name || 'All Departments'}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge className={roleColors[designation.role] || roleColors.employee}>
                        {roleLabels[designation.role] || 'Employee'}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {designation.is_active ? (
                        <Badge className="bg-green-100 text-green-700">Active</Badge>
                      ) : (
                        <Badge variant="secondary">Inactive</Badge>
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleOpenDialog(designation)}
                        >
                          <Pencil className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleToggleActive(designation)}
                        >
                          {designation.is_active ? 'Deactivate' : 'Activate'}
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-red-600 hover:text-red-700"
                          onClick={() => {
                            setDeleteTarget(designation);
                            setShowDeleteDialog(true);
                          }}
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Add/Edit Dialog */}
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>
              {editingDesignation ? 'Edit Designation' : 'Create Designation'}
            </DialogTitle>
            <DialogDescription>
              {editingDesignation ? 'Update designation details and permissions' : 'Add a new job title with role-based access'}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Designation Name *</Label>
              <Input
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="e.g., Senior Manager, Accountant, Store Keeper"
                data-testid="designation-name-input"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Department</Label>
                <Select 
                  value={formData.department_id} 
                  onValueChange={(v) => setFormData({ ...formData, department_id: v })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select department" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Departments</SelectItem>
                    {departments.map(d => (
                      <SelectItem key={d.id} value={d.id}>{d.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Hierarchy Level</Label>
                <Select 
                  value={formData.level.toString()} 
                  onValueChange={(v) => setFormData({ ...formData, level: parseInt(v) })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map(l => (
                      <SelectItem key={l} value={l.toString()}>Level {l} {l === 1 ? '(Entry)' : l === 10 ? '(Executive)' : ''}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="space-y-2">
              <Label>System Role / Permission Level *</Label>
              <Select 
                value={formData.role} 
                onValueChange={(v) => setFormData({ ...formData, role: v })}
              >
                <SelectTrigger data-testid="designation-role-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="admin">
                    <div className="flex items-center gap-2">
                      <Badge className={roleColors.admin}>Admin</Badge>
                      <span className="text-xs text-slate-500">Full access</span>
                    </div>
                  </SelectItem>
                  <SelectItem value="manager">
                    <div className="flex items-center gap-2">
                      <Badge className={roleColors.manager}>Manager</Badge>
                      <span className="text-xs text-slate-500">HR, Inventory, Sales</span>
                    </div>
                  </SelectItem>
                  <SelectItem value="accountant">
                    <div className="flex items-center gap-2">
                      <Badge className={roleColors.accountant}>Accountant</Badge>
                      <span className="text-xs text-slate-500">Finance only</span>
                    </div>
                  </SelectItem>
                  <SelectItem value="store">
                    <div className="flex items-center gap-2">
                      <Badge className={roleColors.store}>Store Keeper</Badge>
                      <span className="text-xs text-slate-500">Inventory only</span>
                    </div>
                  </SelectItem>
                  <SelectItem value="employee">
                    <div className="flex items-center gap-2">
                      <Badge className={roleColors.employee}>Employee</Badge>
                      <span className="text-xs text-slate-500">Portal only</span>
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>
              <p className="text-xs text-slate-500">This determines what menu items the employee can see</p>
            </div>
            <div className="space-y-2">
              <Label>Description (Optional)</Label>
              <Textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Brief description of this designation's responsibilities..."
                rows={2}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleSubmit} data-testid="save-designation-btn">
              {editingDesignation ? 'Update' : 'Create'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Designation?</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete "{deleteTarget?.name}"? 
              {deleteTarget?.is_active && " Employees with this designation will need to be reassigned."}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete} className="bg-red-600 hover:bg-red-700">
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
