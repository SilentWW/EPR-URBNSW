import React, { useState, useEffect } from 'react';
import { payrollAPI } from '../../lib/api';
import { Card, CardContent } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Textarea } from '../../components/ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../../components/ui/dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../../components/ui/table';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '../../components/ui/dropdown-menu';
import { Plus, MoreHorizontal, Pencil, Trash2, Loader2, Building2, Users, AlertTriangle, Sparkles } from 'lucide-react';
import { toast } from 'sonner';

export const Departments = () => {
  const [departments, setDepartments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [seedDialogOpen, setSeedDialogOpen] = useState(false);
  const [selectedDept, setSelectedDept] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [seeding, setSeeding] = useState(false);
  const [formData, setFormData] = useState({ name: '', description: '' });

  const fetchDepartments = async () => {
    try {
      const response = await payrollAPI.getDepartments();
      setDepartments(response.data);
    } catch (error) {
      toast.error('Failed to fetch departments');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDepartments();
  }, []);

  const handleOpenDialog = (dept = null) => {
    if (dept) {
      setSelectedDept(dept);
      setFormData({ name: dept.name, description: dept.description || '' });
    } else {
      setSelectedDept(null);
      setFormData({ name: '', description: '' });
    }
    setDialogOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      if (selectedDept) {
        await payrollAPI.updateDepartment(selectedDept.id, formData);
        toast.success('Department updated successfully');
      } else {
        await payrollAPI.createDepartment(formData);
        toast.success('Department created successfully');
      }
      setDialogOpen(false);
      fetchDepartments();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Operation failed');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async () => {
    try {
      await payrollAPI.deleteDepartment(selectedDept.id);
      toast.success('Department deleted successfully');
      setDeleteDialogOpen(false);
      fetchDepartments();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete department');
    }
  };

  const handleSeedOrgStructure = async () => {
    setSeeding(true);
    try {
      const response = await payrollAPI.seedOrgStructure();
      const data = response.data;
      toast.success(
        `Seeded ${data.departments.created} departments and ${data.designations.created} designations!`,
        { duration: 5000 }
      );
      setSeedDialogOpen(false);
      fetchDepartments();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to seed organization structure');
    } finally {
      setSeeding(false);
    }
  };

  return (
    <div className="space-y-6" data-testid="departments-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900" style={{ fontFamily: 'Outfit, sans-serif' }}>
            Departments
          </h2>
          <p className="text-slate-500 mt-1">{departments.length} departments</p>
        </div>
        <div className="flex gap-2">
          <Button 
            variant="outline" 
            onClick={() => setSeedDialogOpen(true)} 
            className="gap-2"
            data-testid="seed-org-btn"
          >
            <Sparkles className="w-4 h-4" />
            Seed Org Structure
          </Button>
          <Button onClick={() => handleOpenDialog()} className="gap-2 bg-indigo-600 hover:bg-indigo-700" data-testid="add-department-btn">
            <Plus className="w-4 h-4" />
            Add Department
          </Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-indigo-100 rounded-lg">
                <Building2 className="w-5 h-5 text-indigo-600" />
              </div>
              <div>
                <p className="text-sm text-slate-500">Total Departments</p>
                <p className="text-2xl font-bold">{departments.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-emerald-100 rounded-lg">
                <Users className="w-5 h-5 text-emerald-600" />
              </div>
              <div>
                <p className="text-sm text-slate-500">Total Employees</p>
                <p className="text-2xl font-bold">{departments.reduce((sum, d) => sum + (d.employee_count || 0), 0)}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Departments Table */}
      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
            </div>
          ) : departments.length === 0 ? (
            <div className="text-center py-16">
              <Building2 className="w-12 h-12 text-slate-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-slate-900">No departments yet</h3>
              <p className="text-slate-500 mt-1">Create your first department to organize employees.</p>
              <Button onClick={() => handleOpenDialog()} className="mt-4 bg-indigo-600 hover:bg-indigo-700">
                Add Department
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="table-header">
                  <TableHead className="table-header-cell">Department Name</TableHead>
                  <TableHead className="table-header-cell">Description</TableHead>
                  <TableHead className="table-header-cell text-center">Employees</TableHead>
                  <TableHead className="table-header-cell w-12"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {departments.map((dept) => (
                  <TableRow key={dept.id} className="table-row" data-testid={`dept-row-${dept.id}`}>
                    <TableCell className="table-cell font-medium">{dept.name}</TableCell>
                    <TableCell className="table-cell text-slate-500">{dept.description || '-'}</TableCell>
                    <TableCell className="table-cell text-center">
                      <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-slate-100 text-slate-700 font-medium">
                        {dept.employee_count || 0}
                      </span>
                    </TableCell>
                    <TableCell className="table-cell">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon">
                            <MoreHorizontal className="w-4 h-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => handleOpenDialog(dept)}>
                            <Pencil className="w-4 h-4 mr-2" />
                            Edit
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            className="text-red-600"
                            onClick={() => {
                              setSelectedDept(dept);
                              setDeleteDialogOpen(true);
                            }}
                          >
                            <Trash2 className="w-4 h-4 mr-2" />
                            Delete
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Add/Edit Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-md" data-testid="department-dialog">
          <DialogHeader>
            <DialogTitle style={{ fontFamily: 'Outfit, sans-serif' }}>
              {selectedDept ? 'Edit Department' : 'Add Department'}
            </DialogTitle>
            <DialogDescription>
              {selectedDept ? 'Update department information' : 'Create a new department'}
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSubmit}>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="name">Department Name *</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g., Production, Sales, Admin"
                  required
                  data-testid="dept-name-input"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Brief description of the department..."
                  rows={3}
                />
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={submitting} className="bg-indigo-600 hover:bg-indigo-700" data-testid="dept-submit-btn">
                {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                {selectedDept ? 'Update' : 'Create'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-red-600">
              <AlertTriangle className="w-5 h-5" />
              Delete Department
            </DialogTitle>
            <DialogDescription>
              Are you sure you want to delete "{selectedDept?.name}"? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
            <Button variant="destructive" onClick={handleDelete}>Delete</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Seed Organization Structure Dialog */}
      <Dialog open={seedDialogOpen} onOpenChange={setSeedDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-indigo-600" />
              Seed Organization Structure
            </DialogTitle>
            <DialogDescription className="text-left space-y-3 pt-2">
              <p>This will create the following for your clothing brand:</p>
              <ul className="list-disc pl-5 space-y-1 text-sm">
                <li><strong>10 Departments:</strong> Executive, Design, Production, Marketing, E-Commerce, Logistics, Customer Experience, Finance, HR, Legal</li>
                <li><strong>32 Designations:</strong> CEO, Fashion Designer, Production Manager, Brand Manager, etc.</li>
              </ul>
              <p className="text-amber-600 text-sm">Existing departments/designations will be skipped (no duplicates).</p>
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setSeedDialogOpen(false)}>Cancel</Button>
            <Button 
              onClick={handleSeedOrgStructure} 
              disabled={seeding}
              className="bg-indigo-600 hover:bg-indigo-700"
              data-testid="confirm-seed-btn"
            >
              {seeding ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Sparkles className="w-4 h-4 mr-2" />}
              {seeding ? 'Seeding...' : 'Seed Now'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Departments;
