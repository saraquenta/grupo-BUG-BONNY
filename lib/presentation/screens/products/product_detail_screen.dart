import 'package:flutter/material.dart';
import '../../../core/constants/app_colors.dart';
import '../../../data/models/product_model.dart';

class ProductDetailScreen extends StatelessWidget {
  final ProductModel product;

  const ProductDetailScreen({super.key, required this.product});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Detalle de Stock')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Cabecera del producto
            Card(
              elevation: 0,
              color: AppColors.primary.withOpacity(0.05),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Row(
                  children: [
                    Icon(Icons.medication_rounded, size: 48, color: product.stockColor),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(product.name, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                          Text('Código: ${product.code}', style: const TextStyle(color: AppColors.textSecondary, fontSize: 13)),
                          const SizedBox(height: 4),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                            decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(6)),
                            child: Text(product.category, style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold)),
                          )
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 20),

            // Tarjetas de información de Stock e Indicadores mínimos
            Row(
              children: [
                Expanded(
                  child: _buildInfoTile('Stock Total', '${product.currentStock} uds', product.stockColor),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _buildInfoTile('Stock Mínimo', '${product.minStock} uds', AppColors.textSecondary),
                ),
              ],
            ),
            const SizedBox(height: 12),
            _buildInfoTile('Ubicación Física en Almacén', product.location, AppColors.info),

            const SizedBox(height: 24),
            const Text('Control de Lotes y Vencimientos', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
            const SizedBox(height: 12),

            // Tabla/Lista de Lotes (Requerimiento M02 cumplido)
            product.batches.isEmpty
                ? const Card(
                    child: Padding(
                      padding: EdgeInsets.all(16.0),
                      child: Center(child: Text('No hay lotes registrados para este producto.', style: TextStyle(fontSize: 13))),
                    ),
                  )
                : ListView.builder(
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    itemCount: product.batches.length,
                    itemBuilder: (context, index) {
                      final batch = product.batches[index];
                      return Card(
                        margin: const EdgeInsets.symmetric(vertical: 4),
                        child: ListTile(
                          leading: Icon(
                            Icons.layers_rounded,
                            color: batch.isExpired ? AppColors.danger : AppColors.accent,
                          ),
                          title: Text('Lote: ${batch.batchCode}', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                          subtitle: Text(
                            'Vence: ${batch.expirationDate}',
                            style: TextStyle(
                              color: batch.isExpired ? AppColors.danger : AppColors.textSecondary,
                              fontWeight: batch.isExpired ? FontWeight.bold : FontWeight.normal,
                              fontSize: 12,
                            ),
                          ),
                          trailing: Text(
                            '${batch.stock} uds',
                            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                          ),
                        ),
                      );
                    },
                  ),
          ],
        ),
      ),
    );
  }

  Widget _buildInfoTile(String label, String value, Color color) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: const TextStyle(fontSize: 11, color: AppColors.textSecondary)),
          const SizedBox(height: 4),
          Text(value, style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: color)),
        ],
      ),
    );
  }
}