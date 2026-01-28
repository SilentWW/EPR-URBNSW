import React, { useState, useEffect } from 'react';
import { suppliersAPI } from '../lib/api';
import { Card, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '../components/ui/dropdown-menu';
import { Plus, Search, MoreHorizontal, Pencil, Trash2, Loader2, Truck, Eye, AlertTriangle } from 'lucide-react';
import { toast } from 'sonner';

const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-LK', {
    style: 'currency',
    currency: 'LKR',
    minimumFractionDigits: 0,
  }).format(amount);
};

const initialFormData = {
  name: '',
  email: '',
  phone: '',
  address: '',
  contact_person: '',
};

export const Suppliers = () => {
  const [suppliers, setSuppliers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedSupplier, setSelectedSupplier] = useState(null);
  const [supplierDetails, setSupplierDetails] = useState(null);
  const [formData, setFormData] = useState(initialFormData);
  const [submitting, setSubmitting] = useState(false);

  const fetchSuppliers = async () => {
    try {
      const response = await suppliersAPI.getAll(search);
      setSuppliers(response.data);
    } catch (error) {
      toast.error('Failed to fetch suppliers');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSuppliers();
  }, [search]);

  const handleViewSupplier = async (supplier) => {
    try {
      const response = await suppliersAPI.getOne(supplier.id);
      setSupplierDetails(response.data);
      setViewDialogOpen(true);
    } catch (error) {
      toast.error('Failed to load supplier details');
    }
  };

  const handleOpenDialog = (supplier = null) => {
    if (supplier) {
      setSelectedSupplier(supplier);
      setFormData({
        name: supplier.name,
        email: supplier.email || '',
        phone: supplier.phone || '',
        address: supplier.address || '',
        contact_person: supplier.contact_person || '',
      });
    } else {
      setSelectedSupplier(null);
      setFormData(initialFormData);
    }
    setDialogOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);

    try {
      if (selectedSupplier) {
        await suppliersAPI.update(selectedSupplier.id, formData);
        toast.success('Supplier updated successfully');
      } else {
        await suppliersAPI.create(formData);
        toast.success('Supplier created successfully');
      }
      setDialogOpen(false);
      fetchSuppliers();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Operation failed');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async () => {
    try {
      await suppliersAPI.delete(selectedSupplier.id);
      toast.success('Supplier deleted successfully');
      setDeleteDialogOpen(false);
      fetchSuppliers();
    } catch (error) {
      toast.error('Failed to delete supplier');
    }
  };

  return (
    <div className="space-y-6" data-testid="suppliers-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900" style={{ fontFamily: 'Outfit, sans-serif' }}>
            Suppliers
          </h2>
          <p className="text-slate-500 mt-1">{suppliers.length} suppliers in database</p>
        </div>
        <Button onClick={() => handleOpenDialog()} className="gap-2 bg-indigo-600 hover:bg-indigo-700" data-testid="add-supplier-btn">
          <Plus className="w-4 h-4" />
          Add Supplier
        </Button>
      </div>

      {/* Search */}
      <Card>
        <CardContent className="p-4">
          <div className="relative max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <Input
              placeholder="Search suppliers..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9"
              data-testid="search-suppliers"
            />
          </div>
        </CardContent>
      </Card>

      {/* Suppliers Table */}
      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
            </div>
          ) : suppliers.length === 0 ? (
            <div className="text-center py-16">
              <Truck className="w-12 h-12 text-slate-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-slate-900">No suppliers found</h3>
              <p className="text-slate-500 mt-1">Add your first supplier to get started.</p>
              <Button onClick={() => handleOpenDialog()} className="mt-4 bg-indigo-600 hover:bg-indigo-700">
                Add Supplier
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="table-header">
                  <TableHead className="table-header-cell">Company</TableHead>
                  <TableHead className="table-header-cell">Contact Person</TableHead>
                  <TableHead className="table-header-cell">Email</TableHead>
                  <TableHead className="table-header-cell">Phone</TableHead>
                  <TableHead className="table-header-cell w-12"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {suppliers.map((supplier) => (
                  <TableRow key={supplier.id} className="table-row" data-testid={`supplier-row-${supplier.id}`}>
                    <TableCell className="table-cell font-medium">{supplier.name}</TableCell>
                    <TableCell className="table-cell">{supplier.contact_person || '-'}</TableCell>
                    <TableCell className="table-cell text-slate-500">{supplier.email || '-'}</TableCell>
                    <TableCell className="table-cell">{supplier.phone || '-'}</TableCell>
                    <TableCell className="table-cell">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon">
                            <MoreHorizontal className="w-4 h-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => handleViewSupplier(supplier)}>
                            <Eye className="w-4 h-4 mr-2" />
                            View Details
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => handleOpenDialog(supplier)}>
                            <Pencil className="w-4 h-4 mr-2" />
                            Edit
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            className="text-red-600"
                            onClick={() => {
                              setSelectedSupplier(supplier);
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
        <DialogContent className="max-w-md" data-testid="supplier-dialog">
          <DialogHeader>
            <DialogTitle style={{ fontFamily: 'Outfit, sans-serif' }}>
              {selectedSupplier ? 'Edit Supplier' : 'Add New Supplier'}
            </DialogTitle>
            <DialogDescription>
              {selectedSupplier ? 'Update supplier information' : 'Add a new supplier to your database'}
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSubmit}>
            <div className="grid gap-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="name">Company Name *</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                  data-testid="supplier-name"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="contact_person">Contact Person</Label>
                <Input
                  id="contact_person"
                  value={formData.contact_person}
                  onChange={(e) => setFormData({ ...formData, contact_person: e.target.value })}
                  data-testid="supplier-contact"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  data-testid="supplier-email"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="phone">Phone</Label>
                <Input
                  id="phone"
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  data-testid="supplier-phone"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="address">Address</Label>
                <Input
                  id="address"
                  value={formData.address}
                  onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                  data-testid="supplier-address"
                />
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={submitting} className="bg-indigo-600 hover:bg-indigo-700" data-testid="supplier-submit">
                {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                {selectedSupplier ? 'Update' : 'Create'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* View Details Dialog */}
      <Dialog open={viewDialogOpen} onOpenChange={setViewDialogOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle style={{ fontFamily: 'Outfit, sans-serif' }}>Supplier Details</DialogTitle>
          </DialogHeader>
          {supplierDetails && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-slate-500">Company</p>
                  <p className="font-medium">{supplierDetails.name}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Contact Person</p>
                  <p className="font-medium">{supplierDetails.contact_person || '-'}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Email</p>
                  <p className="font-medium">{supplierDetails.email || '-'}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Phone</p>
                  <p className="font-medium">{supplierDetails.phone || '-'}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Total Orders</p>
                  <p className="font-medium">{supplierDetails.total_orders}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Total Amount</p>
                  <p className="font-medium">{formatCurrency(supplierDetails.total_amount)}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Outstanding</p>
                  <p className="font-medium text-amber-600">{formatCurrency(supplierDetails.outstanding_balance)}</p>
                </div>
              </div>
              {supplierDetails.address && (
                <div>
                  <p className="text-sm text-slate-500">Address</p>
                  <p className="font-medium">{supplierDetails.address}</p>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-red-600">
              <AlertTriangle className="w-5 h-5" />
              Delete Supplier
            </DialogTitle>
            <DialogDescription>
              Are you sure you want to delete "{selectedSupplier?.name}"? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
            <Button variant="destructive" onClick={handleDelete}>Delete</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Suppliers;
