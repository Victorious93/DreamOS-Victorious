# AOSP / LineageOS source-tree integration (manual; not yet build-tested)

This repository is a **product customization module**, not a complete AOSP manifest, device tree, kernel or vendor BSP.

## Preconditions

1. Obtain a working AOSP or supported LineageOS source tree for an actual, verified target.
2. Verify device codename, architecture, partition scheme, OS branch, OEM/vendor artifacts, kernel, recovery/OTA path, AVB/verified-boot requirements, rollback indices, and necessary licenses.
3. Successfully build and boot the **unmodified** baseline before attempting DreamOS customizations.
4. Back up user data and confirm that a recovery route exists. No automated flash commands are supplied here.

## Integrate the common product configuration

From this project checkout, copy `aosp/vendor/dreamos/` into `<ANDROID_BUILD_TOP>/vendor/dreamos/`. Inspect the destination before copying; do not overwrite files you have not reviewed. Then, in the existing verified device product makefile, add:

```make
$(call inherit-product, vendor/dreamos/config/common.mk)
```

`common.mk` currently sets `en_US` and `en_GB` ordering and installs a static edition metadata file at `$(TARGET_COPY_OUT_PRODUCT)/etc/dreamos/edition.conf`. Inheriting it may change a product's locale list: review and merge this policy with the existing product. This is **not** an alternate `AndroidProducts.mk`, `BoardConfig.mk`, or device-specific product definition.

Use the existing Android branch's documented `lunch` target and build commands. This project does not invent a universal lunch target or release ZIP. Do not build or flash without knowing the target-specific commands.

## What Phase 1 does not do

- No modifications to SELinux policy, kernel, vendor blobs, userdata, partition layouts, AVB, verified boot, or bootloader state.
- No system-privileged location service, hook framework, root manager, device identity modification, or anti-detection feature.
- No VMOS/vPhone importable image: the virtual-profile field represents a planned compatibility track only.

## Provenance and build validation

A full Android compile must be performed with an actual checked-out Android platform tree. Host-only Python unit tests and source ZIP verification do **not** establish that the product inherits successfully or that an OS boots.
