# DreamOS architecture

```text
User-approved target specifications
               |
               v
      profiles/*.json
               |
       validate_profile
               |
               v
    source-bundle factory ---------> SHA-256 manifest & verifier
               |
               v
   vendor/dreamos/config/common.mk
               |
               v
 Verified AOSP/Lineage device product  [FUTURE; external platform tree]
           /           \
 physical build       virtual build adapter  [both FUTURE]
 ROM OTA/image         VMOS / vPhone format   [device/vendor specific]
```

Phase 1 is **not** an Android kernel, phone app, privileged framework or executable ROM. It builds validated product source integration bundles. Future Android modules must be built and tested against a selected platform tree, and physical/virtual producers must use their own compatibility contracts.
