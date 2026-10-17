# DreamOS Victorious - shared product configuration, not a device/board definition.
# Include from a verified device product .mk in an AOSP build tree:
#   $(call inherit-product, vendor/dreamos/config/common.mk)
# Deliberately preserves SELinux, verified boot, encryption and upstream build settings.
# English appears first to provide an English default when the product adopts this list.
PRODUCT_LOCALES := en_US en_GB
PRODUCT_COPY_FILES += \
    vendor/dreamos/config/edition.conf:$(TARGET_COPY_OUT_PRODUCT)/etc/dreamos/edition.conf
# No custom ro.* properties: these would require a proper property policy declaration.
# No root binaries, Xposed, mock-location services or proprietary APKs bundled.
