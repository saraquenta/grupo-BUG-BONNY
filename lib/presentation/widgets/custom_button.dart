import 'package:flutter/material.dart';
import '../../core/constants/app_colors.dart';

class CustomButton extends StatelessWidget {
  final String      label;
  final VoidCallback? onPressed;
  final bool        isLoading;
  final Color       backgroundColor;
  final Color       textColor;
  final IconData?   icon;
  final double      height;

  const CustomButton({
    super.key,
    required this.label,
    this.onPressed,
    this.isLoading    = false,
    this.backgroundColor = AppColors.primary,
    this.textColor    = Colors.white,
    this.icon,
    this.height       = 52,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width:  double.infinity,
      height: height,
      child: ElevatedButton(
        onPressed: isLoading ? null : onPressed,
        style: ElevatedButton.styleFrom(
          backgroundColor: backgroundColor,
          foregroundColor: textColor,
          disabledBackgroundColor: backgroundColor.withOpacity(0.6),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
          elevation: 0,
        ),
        child: isLoading
            ? SizedBox(
                height: 22,
                width:  22,
                child: CircularProgressIndicator(
                  color:       textColor,
                  strokeWidth: 2.5,
                ),
              )
            : Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  if (icon != null) ...[
                    Icon(icon, size: 20),
                    const SizedBox(width: 8),
                  ],
                  Text(
                    label,
                    style: TextStyle(
                      fontSize:   16,
                      fontWeight: FontWeight.w600,
                      color:      textColor,
                    ),
                  ),
                ],
              ),
      ),
    );
  }
}
