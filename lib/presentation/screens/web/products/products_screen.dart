import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../../../core/constants/app_colors.dart';
import '../../../../providers_web/products_provider.dart';

class WebProductsScreen extends StatefulWidget {
  const WebProductsScreen({super.key});

  @override
  State<WebProductsScreen> createState() => _WebProductsScreenState();
}

class _WebProductsScreenState extends State<WebProductsScreen> {
  final _searchController = TextEditingController();
  String? _selectedCategoryId;
  String? _selectedStockFilter;
  int _currentPage = 0;
  final int _rowsPerPage = 10;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<WebProductsProvider>().loadProducts();
      context.read<WebProductsProvider>().loadCategories();
    });
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  void _applyFilters() {
    context.read<WebProductsProvider>().setFilters(
          search:
              _searchController.text.isNotEmpty ? _searchController.text : null,
          categoryId: _selectedCategoryId != null
              ? int.tryParse(_selectedCategoryId!)
              : null,
          lowStock: _selectedStockFilter == 'low'
              ? true
              : _selectedStockFilter == 'critical'
                  ? true
                  : null,
        );
    setState(() => _currentPage = 0);
  }

  void _clearFilters() {
    _searchController.clear();
    setState(() {
      _selectedCategoryId = null;
      _selectedStockFilter = null;
      _currentPage = 0;
    });
    context.read<WebProductsProvider>().clearFilters();
  }

  @override
  Widget build(BuildContext context) {
    final productsProvider = Provider.of<WebProductsProvider>(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Productos'),
        elevation: 0,
        backgroundColor: AppColors.primary,
      ),
      body: Column(
        children: [
          // Filtros
          Container(
            padding: const EdgeInsets.all(16),
            color: Colors.white,
            child: Row(
              children: [
                Expanded(
                  flex: 2,
                  child: TextField(
                    controller: _searchController,
                    decoration: const InputDecoration(
                      hintText: 'Buscar por nombre o código...',
                      prefixIcon: Icon(Icons.search),
                      border: OutlineInputBorder(),
                    ),
                    onSubmitted: (_) => _applyFilters(),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: DropdownButtonFormField<String>(
                    value: _selectedCategoryId,
                    decoration: const InputDecoration(
                      hintText: 'Todas las categorías',
                      border: OutlineInputBorder(),
                    ),
                    items: [
                      const DropdownMenuItem(
                          value: null, child: Text('Todas las categorías')),
                      ...productsProvider.categories.map((cat) {
                        return DropdownMenuItem(
                          value: cat['id'].toString(),
                          child: Text(cat['name']),
                        );
                      }),
                    ],
                    onChanged: (value) {
                      setState(() => _selectedCategoryId = value);
                      _applyFilters();
                    },
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: DropdownButtonFormField<String>(
                    value: _selectedStockFilter,
                    decoration: const InputDecoration(
                      hintText: 'Todos los stocks',
                      border: OutlineInputBorder(),
                    ),
                    items: const [
                      DropdownMenuItem(
                          value: null, child: Text('Todos los stocks')),
                      DropdownMenuItem(value: 'low', child: Text('Stock Bajo')),
                      DropdownMenuItem(
                          value: 'critical', child: Text('Stock Crítico')),
                    ],
                    onChanged: (value) {
                      setState(() => _selectedStockFilter = value);
                      _applyFilters();
                    },
                  ),
                ),
                const SizedBox(width: 12),
                ElevatedButton.icon(
                  onPressed: _clearFilters,
                  icon: const Icon(Icons.clear),
                  label: const Text('Limpiar'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.grey,
                  ),
                ),
                const SizedBox(width: 12),
                ElevatedButton.icon(
                  onPressed: () => _showProductModal(context),
                  icon: const Icon(Icons.add),
                  label: const Text('Nuevo Producto'),
                ),
              ],
            ),
          ),

          // Tabla de productos
          Expanded(
            child: productsProvider.isLoading
                ? const Center(child: CircularProgressIndicator())
                : productsProvider.error != null
                    ? Center(child: Text(productsProvider.error!))
                    : productsProvider.products.isEmpty
                        ? const Center(child: Text('No hay productos'))
                        : SingleChildScrollView(
                            scrollDirection: Axis.horizontal,
                            child: DataTable(
                              columnSpacing: 16,
                              headingRowColor: WidgetStateProperty.resolveWith(
                                (states) => Colors.grey[200],
                              ),
                              columns: const [
                                DataColumn(label: Text('Código')),
                                DataColumn(label: Text('Nombre')),
                                DataColumn(label: Text('Categoría')),
                                DataColumn(label: Text('Stock Actual')),
                                DataColumn(label: Text('Stock Mínimo')),
                                DataColumn(label: Text('Estado')),
                                DataColumn(label: Text('Acciones')),
                              ],
                              rows: productsProvider.products
                                  .skip(_currentPage * _rowsPerPage)
                                  .take(_rowsPerPage)
                                  .map((product) {
                                final currentStock =
                                    (product['current_stock'] ?? 0).toDouble();
                                final minStock =
                                    (product['min_stock'] ?? 0).toDouble();
                                final isLowStock = currentStock <= minStock;
                                final isCritical = currentStock <= 0;
                                Color stockColor;
                                String stockStatus;

                                if (isCritical) {
                                  stockColor = Colors.red;
                                  stockStatus = 'Crítico';
                                } else if (isLowStock) {
                                  stockColor = Colors.orange;
                                  stockStatus = 'Bajo';
                                } else {
                                  stockColor = Colors.green;
                                  stockStatus = 'OK';
                                }

                                return DataRow(
                                  cells: [
                                    DataCell(Text(product['code'] ?? 'N/A')),
                                    DataCell(Text(product['name'] ?? 'N/A')),
                                    DataCell(Text(product['category']
                                            ?['name'] ??
                                        'Sin categoría')),
                                    DataCell(Text(currentStock.toString())),
                                    DataCell(Text(minStock.toString())),
                                    DataCell(
                                      Container(
                                        padding: const EdgeInsets.symmetric(
                                            horizontal: 8, vertical: 4),
                                        decoration: BoxDecoration(
                                          color:
                                              stockColor.withValues(alpha: 0.1),
                                          borderRadius:
                                              BorderRadius.circular(12),
                                        ),
                                        child: Row(
                                          mainAxisSize: MainAxisSize.min,
                                          children: [
                                            Container(
                                              width: 8,
                                              height: 8,
                                              decoration: BoxDecoration(
                                                shape: BoxShape.circle,
                                                color: stockColor,
                                              ),
                                            ),
                                            const SizedBox(width: 4),
                                            Text(
                                              stockStatus,
                                              style: TextStyle(
                                                  color: stockColor,
                                                  fontSize: 12),
                                            ),
                                          ],
                                        ),
                                      ),
                                    ),
                                    DataCell(
                                      Row(
                                        children: [
                                          IconButton(
                                            icon: const Icon(Icons.edit,
                                                size: 20),
                                            color: AppColors.primary,
                                            onPressed: () => _showProductModal(
                                              context,
                                              product: product,
                                            ),
                                          ),
                                          IconButton(
                                            icon: const Icon(Icons.delete,
                                                size: 20),
                                            color: Colors.red,
                                            onPressed: () {
                                              final productId = product['id'];
                                              if (productId != null) {
                                                _confirmDelete(
                                                    context, productId);
                                              }
                                            },
                                          ),
                                        ],
                                      ),
                                    ),
                                  ],
                                );
                              }).toList(),
                            ),
                          ),
          ),

          // Paginación
          if (productsProvider.products.isNotEmpty)
            Container(
              padding: const EdgeInsets.all(16),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  Text(
                      'Página ${_currentPage + 1} de ${(productsProvider.products.length / _rowsPerPage).ceil()}'),
                  IconButton(
                    icon: const Icon(Icons.chevron_left),
                    onPressed: _currentPage > 0
                        ? () => setState(() => _currentPage--)
                        : null,
                  ),
                  IconButton(
                    icon: const Icon(Icons.chevron_right),
                    onPressed: (_currentPage + 1) * _rowsPerPage <
                            productsProvider.products.length
                        ? () => setState(() => _currentPage++)
                        : null,
                  ),
                ],
              ),
            ),
        ],
      ),
    );
  }

  void _showProductModal(BuildContext context,
      {Map<String, dynamic>? product}) {
    final isEditing = product != null;

    // Usar controllers con texto inicial
    final nameController = TextEditingController(
        text: product != null ? (product['name'] ?? '') : '');
    final codeController = TextEditingController(
        text: product != null ? (product['code'] ?? '') : '');
    final minStockController = TextEditingController(
        text: product != null ? (product['min_stock'] ?? 5).toString() : '5');
    final currentStockController = TextEditingController(
        text:
            product != null ? (product['current_stock'] ?? 0).toString() : '0');
    String? selectedCategoryId =
        product != null ? product['category_id']?.toString() : null;

    showDialog(
      context: context,
      builder: (dialogContext) {
        return StatefulBuilder(
          builder: (context, setModalState) {
            return AlertDialog(
              title: Text(isEditing ? 'Editar Producto' : 'Nuevo Producto'),
              content: SizedBox(
                width: 500,
                child: SingleChildScrollView(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      TextField(
                        controller: codeController,
                        decoration: const InputDecoration(
                          labelText: 'Código *',
                          border: OutlineInputBorder(),
                        ),
                      ),
                      const SizedBox(height: 12),
                      TextField(
                        controller: nameController,
                        decoration: const InputDecoration(
                          labelText: 'Nombre *',
                          border: OutlineInputBorder(),
                        ),
                      ),
                      const SizedBox(height: 12),
                      DropdownButtonFormField<String>(
                        value: selectedCategoryId,
                        decoration: const InputDecoration(
                          labelText: 'Categoría',
                          border: OutlineInputBorder(),
                        ),
                        items: [
                          const DropdownMenuItem(
                              value: null, child: Text('Sin categoría')),
                          ...context
                              .read<WebProductsProvider>()
                              .categories
                              .map((cat) {
                            return DropdownMenuItem(
                              value: cat['id'].toString(),
                              child: Text(cat['name']),
                            );
                          }),
                        ],
                        onChanged: (value) =>
                            setModalState(() => selectedCategoryId = value),
                      ),
                      const SizedBox(height: 12),
                      TextField(
                        controller: minStockController,
                        keyboardType: TextInputType.number,
                        decoration: const InputDecoration(
                          labelText: 'Stock Mínimo',
                          border: OutlineInputBorder(),
                        ),
                      ),
                      const SizedBox(height: 12),
                      TextField(
                        controller: currentStockController,
                        keyboardType: TextInputType.number,
                        decoration: const InputDecoration(
                          labelText: 'Stock Actual',
                          border: OutlineInputBorder(),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.pop(dialogContext),
                  child: const Text('Cancelar'),
                ),
                ElevatedButton(
                  onPressed: () async {
                    final data = {
                      'code': codeController.text,
                      'name': nameController.text,
                      'min_stock':
                          double.tryParse(minStockController.text) ?? 5,
                      'current_stock':
                          double.tryParse(currentStockController.text) ?? 0,
                      if (selectedCategoryId != null &&
                          selectedCategoryId!.isNotEmpty)
                        'category_id': int.parse(selectedCategoryId!),
                    };

                    bool success;
                    if (isEditing && product != null) {
                      success = await context
                          .read<WebProductsProvider>()
                          .updateProduct(product['id'], data);
                    } else {
                      success = await context
                          .read<WebProductsProvider>()
                          .createProduct(data);
                    }

                    if (success && mounted) {
                      Navigator.pop(dialogContext);
                    }
                  },
                  child: Text(isEditing ? 'Guardar' : 'Crear'),
                ),
              ],
            );
          },
        );
      },
    );
  }

  void _confirmDelete(BuildContext context, int productId) {
    showDialog(
      context: context,
      builder: (dialogContext) {
        return AlertDialog(
          title: const Text('Eliminar Producto'),
          content:
              const Text('¿Estás seguro de que deseas eliminar este producto?'),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(dialogContext),
              child: const Text('Cancelar'),
            ),
            ElevatedButton(
              onPressed: () async {
                final success = await context
                    .read<WebProductsProvider>()
                    .deleteProduct(productId);
                if (success && mounted) {
                  if (mounted) {
                    Navigator.pop(dialogContext);
                  }
                }
              },
              style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
              child: const Text('Eliminar'),
            ),
          ],
        );
      },
    );
  }
}
