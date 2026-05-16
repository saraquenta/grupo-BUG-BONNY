import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../../core/constants/app_colors.dart';
import '../../../providers/product_provider.dart';
import 'product_detail_screen.dart';

class ProductsScreen extends StatefulWidget {
  const ProductsScreen({super.key});

  @override
  State<ProductsScreen> createState() => _ProductsScreenState();
}

class _ProductsScreenState extends State<ProductsScreen> {
  final TextEditingController _searchController = TextEditingController();

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<ProductProvider>().fetchProducts();
    });
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final productProvider = context.watch<ProductProvider>();

    return Scaffold(
      appBar: AppBar(
        title: const Text('Inventario de Productos',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
      ),
      body: Column(
        children: [
          // Filtros horizontales por categorías
          if (!productProvider.isLoading &&
              productProvider.errorMessage.isEmpty)
            Container(
              height: 40,
              margin: const EdgeInsets.only(top: 12, left: 12),
              child: ListView.builder(
                scrollDirection: Axis.horizontal,
                itemCount: productProvider.categories.length,
                itemBuilder: (context, index) {
                  final cat = productProvider.categories[index];
                  final isSelected = productProvider.selectedCategory == cat;
                  return Padding(
                    padding: const EdgeInsets.only(right: 8.0),
                    child: ChoiceChip(
                      label: Text(cat,
                          style: TextStyle(
                              fontSize: 12,
                              color: isSelected
                                  ? Colors.white
                                  : AppColors.textPrimary)),
                      selected: isSelected,
                      selectedColor: AppColors.primary,
                      backgroundColor: AppColors.surface,
                      onSelected: (_) => productProvider.filterByCategory(cat),
                    ),
                  );
                },
              ),
            ),

          // Buscador y Control de Stock Crítico
          Padding(
            padding: const EdgeInsets.all(12.0),
            child: Column(
              children: [
                TextField(
                  controller: _searchController,
                  onChanged: productProvider.filterProducts,
                  decoration: InputDecoration(
                    hintText: 'Buscar por nombre o código...',
                    prefixIcon: const Icon(Icons.search),
                    border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(12)),
                    contentPadding: const EdgeInsets.symmetric(vertical: 0),
                  ),
                ),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Text('Mostrar solo stock crítico',
                        style: TextStyle(
                            fontSize: 13, fontWeight: FontWeight.w500)),
                    Switch.adaptive(
                      value: productProvider.filterByCriticalStock,
                      activeColor: AppColors.danger,
                      onChanged: productProvider.toggleCriticalStockFilter,
                    ),
                  ],
                ),
              ],
            ),
          ),

          // Listado Dinámico de Resultados
          Expanded(
            child: productProvider.isLoading
                ? const Center(
                    child: CircularProgressIndicator(color: AppColors.primary))
                : productProvider.errorMessage.isNotEmpty
                    ? Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Text(
                              productProvider.errorMessage,
                              style: const TextStyle(color: AppColors.danger),
                              textAlign: TextAlign
                                  .center, 
                            ),
                            const SizedBox(height: 12),
                            ElevatedButton(
                              onPressed: () => productProvider.fetchProducts(),
                              child: const Text('Reintentar'),
                            )
                          ],
                        ),
                      )
                    : productProvider.products.isEmpty
                        ? const Center(
                            child: Text(
                                'No se encontraron productos en esta sección.'))
                        : RefreshIndicator(
                            onRefresh: () => productProvider.fetchProducts(),
                            child: ListView.builder(
                              padding:
                                  const EdgeInsets.symmetric(horizontal: 12),
                              itemCount: productProvider.products.length,
                              itemBuilder: (context, index) {
                                final product = productProvider.products[index];
                                return Card(
                                  margin:
                                      const EdgeInsets.symmetric(vertical: 6),
                                  shape: RoundedRectangleBorder(
                                    borderRadius: BorderRadius.circular(12),
                                    side: BorderSide(
                                        color: product.isStockCritical
                                            ? AppColors.danger.withOpacity(0.3)
                                            : Colors.transparent),
                                  ),
                                  child: ListTile(
                                    contentPadding: const EdgeInsets.all(12),
                                    title: Text(product.name,
                                        style: const TextStyle(
                                            fontWeight: FontWeight.bold,
                                            fontSize: 14)),
                                    subtitle: Text(
                                        'Código: ${product.code} | Cat: ${product.category}',
                                        style: const TextStyle(fontSize: 11)),
                                    trailing: Container(
                                      padding: const EdgeInsets.symmetric(
                                          horizontal: 10, vertical: 6),
                                      decoration: BoxDecoration(
                                        color: product.stockColor
                                            .withOpacity(0.12),
                                        borderRadius: BorderRadius.circular(8),
                                      ),
                                      child: Text(
                                        'Stock: ${product.currentStock}',
                                        style: TextStyle(
                                            color: product.stockColor,
                                            fontWeight: FontWeight.bold,
                                            fontSize: 13),
                                      ),
                                    ),
                                    onTap: () {
                                      Navigator.push(
                                        context,
                                        MaterialPageRoute(
                                          builder: (context) =>
                                              ProductDetailScreen(
                                                  product: product),
                                        ),
                                      );
                                    },
                                  ),
                                );
                              },
                            ),
                          ),
          ),
        ],
      ),
    );
  }
}
