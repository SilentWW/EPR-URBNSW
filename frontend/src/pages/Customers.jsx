import React, { useState, useEffect } from 'react';
import { customersAPI } from '../lib/api';
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
import { Plus, Search, MoreHorizontal, Pencil, Trash2, Loader2, Users, Eye, AlertTriangle } from 'lucide-react';
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
};

export const Customers = () => {
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [customerDetails, setCustomerDetails] = useState(null);
  const [formData, setFormData] = useState(initialFormData);
  const [submitting, setSubmitting] = useState(false);

  const fetchCustomers = async () => {
    try {
      const response = await customersAPI.getAll(search);
      setCustomers(response.data);
    } catch (error) {
      toast.error('Failed to fetch customers');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCustomers();
  }, [search]);

  const handleViewCustomer = async (customer) => {
    try {
      const response = await customersAPI.getOne(customer.id);
      setCustomerDetails(response.data);
      setViewDialogOpen(true);
    } catch (error) {
      toast.error('Failed to load customer details');
    }
  };

  const handleOpenDialog = (customer = null) => {
    if (customer) {
      setSelectedCustomer(customer);
      setFormData({
        name: customer.name,
        email: customer.email || '',
        phone: customer.phone || '',
        address: customer.address || '',
      });
    } else {
      setSelectedCustomer(null);
      setFormData(initialFormData);
    }
    setDialogOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);

    try {
      if (selectedCustomer) {
        await customersAPI.update(selectedCustomer.id, formData);
        toast.success('Customer updated successfully');
      } else {
        await customersAPI.create(formData);
        toast.success('Customer created successfully');
      }
      setDialogOpen(false);
      fetchCustomers();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Operation failed');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async () => {
    try {
      await customersAPI.delete(selectedCustomer.id);
      toast.success('Customer deleted successfully');
      setDeleteDialogOpen(false);
      fetchCustomers();
    } catch (error) {
      toast.error('Failed to delete customer');
    }
  };

  return (
    <div className="space-y-6" data-testid="customers-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900" style={{ fontFamily: 'Outfit, sans-serif' }}>
            Customers
          </h2>
          <p className="text-slate-500 mt-1">{customers.length} customers in database</p>
        </div>
        <Button onClick={() => handleOpenDialog()} className="gap-2 bg-indigo-600 hover:bg-indigo-700" data-testid="add-customer-btn">
          <Plus className="w-4 h-4" />
          Add Customer
        </Button>
      </div>

      {/* Search */}
      <Card>
        <CardContent className="p-4">
          <div className="relative max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <Input
              placeholder="Search customers..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9"
              data-testid="search-customers"
            />
          </div>
        </CardContent>
      </Card>

      {/* Customers Table */}
      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
            </div>
          ) : customers.length === 0 ? (
            <div className="text-center py-16">
              <Users className="w-12 h-12 text-slate-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-slate-900">No customers found</h3>
              <p className="text-slate-500 mt-1">Add your first customer to get started.</p>
              <Button onClick={() => handleOpenDialog()} className="mt-4 bg-indigo-600 hover:bg-indigo-700">
                Add Customer
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="table-header">
                  <TableHead className="table-header-cell">Name</TableHead>
                  <TableHead className="table-header-cell">Email</TableHead>
                  <TableHead className="table-header-cell">Phone</TableHead>
                  <TableHead className="table-header-cell">Address</TableHead>
                  <TableHead className="table-header-cell w-12"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {customers.map((customer) => (
                  <TableRow key={customer.id} className="table-row" data-testid={`customer-row-${customer.id}`}>
                    <TableCell className="table-cell font-medium">{customer.name}</TableCell>
                    <TableCell className="table-cell text-slate-500">{customer.email || '-'}</TableCell>
                    <TableCell className="table-cell">{customer.phone || '-'}</TableCell>
                    <TableCell className="table-cell text-slate-500 max-w-xs truncate">
                      {customer.address || '-'}
                    </TableCell>
                    <TableCell className="table-cell">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon">
                            <MoreHorizontal className="w-4 h-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => handleViewCustomer(customer)}>
                            <Eye className="w-4 h-4 mr-2" />
                            View Details
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => handleOpenDialog(customer)}>
                            <Pencil className="w-4 h-4 mr-2" />
                            Edit
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            className="text-red-600"
                            onClick={() => {
                              setSelectedCustomer(customer);
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
        <DialogContent className="max-w-md" data-testid="customer-dialog">
          <DialogHeader>
            <DialogTitle style={{ fontFamily: 'Outfit, sans-serif' }}>
              {selectedCustomer ? 'Edit Customer' : 'Add New Customer'}
            </DialogTitle>
            <DialogDescription>
              {selectedCustomer ? 'Update customer information' : 'Add a new customer to your database'}
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSubmit}>
            <div className="grid gap-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="name">Name *</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                  data-testid="customer-name"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  data-testid="customer-email"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="phone">Phone</Label>
                <Input
                  id="phone"
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  data-testid="customer-phone"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="address">Address</Label>
                <Input
                  id="address"
                  value={formData.address}
                  onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                  data-testid="customer-address"
                />
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={submitting} className="bg-indigo-600 hover:bg-indigo-700" data-testid="customer-submit">
                {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                {selectedCustomer ? 'Update' : 'Create'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* View Details Dialog */}
      <Dialog open={viewDialogOpen} onOpenChange={setViewDialogOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle style={{ fontFamily: 'Outfit, sans-serif' }}>Customer Details</DialogTitle>
          </DialogHeader>
          {customerDetails && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-slate-500">Name</p>
                  <p className="font-medium">{customerDetails.name}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Email</p>
                  <p className="font-medium">{customerDetails.email || '-'}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Phone</p>
                  <p className="font-medium">{customerDetails.phone || '-'}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Total Orders</p>
                  <p className="font-medium">{customerDetails.total_orders}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Total Spent</p>
                  <p className="font-medium">{formatCurrency(customerDetails.total_spent)}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Outstanding</p>
                  <p className="font-medium text-amber-600">{formatCurrency(customerDetails.outstanding_balance)}</p>
                </div>
              </div>
              {customerDetails.address && (
                <div>
                  <p className="text-sm text-slate-500">Address</p>
                  <p className="font-medium">{customerDetails.address}</p>
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
              Delete Customer
            </DialogTitle>
            <DialogDescription>
              Are you sure you want to delete "{selectedCustomer?.name}"? This action cannot be undone.
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

export default Customers;
