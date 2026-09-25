# T-shirt Preview --- Current State and Codex Handover

## Purpose

This document captures the current state of the dynamic T-shirt preview
work in the Django/Oscar project so that a new Codex thread in PyCharm
can continue without reconstructing the earlier discussion.

**Project root**

`/Users/david/PycharmProjects/DjangoProject/Topository_01`

The application is a Django project using Django Oscar for the
shop/catalogue.

## Current objective

Parent catalogue products represent designs. Child products represent
purchasable T-shirt variants with attributes including:

-   T-shirt style, e.g. `AS-5001`
-   colour
-   size

The product detail page lets the customer select style, colour and size
and displays a dynamically rendered preview of the design on the
selected T-shirt.

The preview must preserve enough photographic seam, fold and wrinkle
information to communicate the physical T-shirt style accurately.

## Important files

Inspect these before changing anything:

-   `topository_01/views.py` --- dynamic preview renderer, including
    `tshirt_preview`
-   root `urls.py` --- route for the preview endpoint
-   `utils/build_tshirt_assets.py` --- generates the reusable base and
    mask for a T-shirt style
-   `templates/oscar/catalogue/detail.html` --- product variant UI and
    preview display
-   `static/topository/colours_parsed.json` --- colour-name to hex
    mapping
-   `media/base_style_images/<style>.png` --- source style photographs
-   `static/topository/tshirts/<style>/<style>_base.png`
-   `static/topository/tshirts/<style>/<style>_mask.png`

Example AS-5001 assets:

`media/base_style_images/AS-5001.png`

`static/topository/tshirts/AS-5001/AS-5001_base.png`

`static/topository/tshirts/AS-5001/AS-5001_mask.png`

## URL routing

The project has a dynamic preview route before the Oscar URL include,
conceptually:

``` python
path(
    "tshirt-preview/<int:child_id>/",
    views.tshirt_preview,
    name="tshirt_preview",
)
```

Do not move this behind Oscar's catch-all catalogue routing.

## Oscar product attributes

The current product data uses:

-   `child.attr.colour`
-   `child.attr.tshirt_style`

These may be plain values or Oscar `AttributeOption` objects. Existing
code normalises an `AttributeOption` using its `.option` value.

Do not revert to older attribute names such as `tshirt_style_code` or
`tshirt_style_name`.

## Parent design image

The design comes from the child product's parent:

``` python
parent = child.parent or child
```

In the Oscar version used by this project, `primary_image` is callable.
The existing implementation deliberately handles this and uses the
original uploaded image:

``` python
primary_image_attr = getattr(parent, "primary_image", None)

if callable(primary_image_attr):
    primary_image_model = primary_image_attr()
else:
    primary_image_model = primary_image_attr

design_path = primary_image_model.original.path
```

Do not change this to `parent.primary_image.original.path`; that
previously failed because `primary_image` is a method.

## Colour lookup

`static/topository/colours_parsed.json` maps normalised colour names to
hex values.

The lookup key is currently produced approximately as:

``` python
key = colour.strip().lower().replace(" ", "_")
```

The hex value is converted to RGB before rendering.

## Style asset generation

`utils/build_tshirt_assets.py` is a standalone utility within the Django
project. It is not a Django view.

Normal usage from the project root is:

``` zsh
python3 utils/build_tshirt_assets.py --style AS-5001
```

The default input is:

`media/base_style_images/AS-5001.png`

The outputs are:

`static/topository/tshirts/AS-5001/AS-5001_base.png`

`static/topository/tshirts/AS-5001/AS-5001_mask.png`

The mask is intended primarily to isolate the T-shirt silhouette.
Seam/wrinkle information should come from the photographic base, not be
encoded artificially into the mask.

The base-generation code was recently adjusted away from an excessive
brightness factor of `2.0`. The intention is to retain real fabric
luminance detail without blowing out the source.

Before modifying this utility, inspect its actual current contents.
There has previously been a duplicate/incorrect editor buffer containing
a simplified mask implementation; use the real
`utils/build_tshirt_assets.py` in the project.

## Current dynamic rendering pipeline

The current `tshirt_preview(request, child_id)` broadly does this:

1.  Load the Oscar child product.
2.  Resolve its colour and `tshirt_style`.
3.  Look up the selected colour's hex value.
4.  Load the reusable base and mask for the style.
5.  Resolve the parent product's original design image.
6.  Convert the selected hex colour to RGB.
7.  Tint the shirt while retaining base-image luminance.
8.  Place the design on the chest.
9.  Re-impose some wrinkle/seam texture.
10. Composite onto a near-white background.
11. Return the generated PNG directly from memory as a Django
    `HttpResponse`.

The preview is intentionally generated dynamically because parent design
artwork may change later.

## Current rendering problem --- highest priority

The latest tests exposed a colour-dependent problem.

### Very light shirt colours

Very light colours show excessive dark shadowing/folds. The shirt looks
dirty or heavily creased rather than naturally textured.

### Very dark shirt colours

Very dark colours show conspicuous whitish/chalky spots in highlighted
areas of the fabric.

### Required direction

Optimise wrinkle/seam rendering according to the selected shirt colour's
hex value.

This should happen in the dynamic renderer (`views.py`), because one
base/mask pair is shared by all colours of a style. Do not generate
separate base images for every colour unless there is a compelling
technical reason.

The intended approach is to derive perceptual luminance from the
selected RGB colour and use it to control the wrinkle/shading
transformation.

For example:

``` python
luminance = 0.299 * r + 0.587 * g + 0.114 * b
```

However, do not blindly apply previously suggested threshold values.
Inspect the current renderer first and design a coherent solution.

## Important issue in the current renderer

At the time this handover was created, `views.py` contained strong,
fixed wrinkle enhancement approximately equivalent to:

``` python
factor = 0.35 + lum * 0.75
```

This is applied while tinting the shirt.

There is also a second wrinkle/seam pass in `place_design_on_shirt`,
again using a strong fixed range.

That means fabric contrast can effectively be applied twice. This is
likely contributing to the excessive shadows on pale shirts.

The next implementation should examine the entire tonal pipeline rather
than simply adding another brightness/contrast adjustment on top.

## Desired rendering behaviour

The renderer should aim for:

-   **Very light colours:** subtle but visible seams/folds; no
    dirty-looking deep shadows.
-   **Light/mid colours:** natural photographic fabric detail.
-   **Mid colours:** enough contrast to communicate garment
    construction.
-   **Dark colours:** visible folds/seams without white/chalky highlight
    spots.
-   **Very dark/black colours:** preserve shape and construction detail
    without turning highlights grey-white.

Prefer a continuous luminance-based interpolation over abrupt colour
categories if practical.

Also consider separating shadow modulation from highlight modulation. A
single multiplicative factor range may not be ideal for both extremes.

## Design artwork

The T-shirt texture should not damage or excessively alter the design
artwork.

The earlier goal of re-imposing wrinkles over the design was to make the
print appear to sit on fabric rather than float above it. This should be
subtle. The design itself must not receive the same aggressive tonal
treatment as the shirt.

If necessary, use a much weaker texture strength over the design region
than over the unprinted shirt.

## Product detail UI already implemented

The product page has variant selection for:

-   style
-   colour swatches
-   size

Swatches use `colours_parsed.json`, are square/equal size, sorted
alphabetically by display name, and use tooltips for names.

Sizes display in natural order from XS upward.

The page also contains a dynamic T-shirt preview panel below the main
design image and to the left of the selection panel.

Do not redesign this UI unless specifically asked.

## Known resolved issues

Do not spend time re-investigating these unless they recur:

-   Preview endpoint 404 caused by URL ordering --- resolved.
-   Oscar `primary_image` being a method --- resolved.
-   Missing style base/mask files --- resolved once generated.
-   Earlier horizontal white stripe below the design --- considered
    resolved.
-   Dynamic generation is intentional; do not replace it with manually
    generated static previews.

## Planned later improvements

These are wanted, but they are not the immediate task:

1.  Cache generated previews so identical previews are not repeatedly
    rendered.
2.  Support multiple design regions such as front/back/sleeve.
3.  Support per-style chest-placement overrides.
4.  Generate WebP rather than PNG for faster delivery.
5.  Add subtle transparent shadows for greater realism.

First get colour-dependent fabric rendering correct.

## Working approach for Codex

Before making changes:

1.  Inspect `topository_01/views.py`.
2.  Inspect the real `utils/build_tshirt_assets.py`.
3.  Inspect `colours_parsed.json`.
4.  Locate the AS-5001 base and mask assets.
5.  Summarise the current rendering pipeline and identify where tonal
    adjustment is being applied.
6.  Propose the smallest coherent change to solve both the pale-shirt
    shadow problem and dark-shirt chalky-highlight problem.
7.  Do not modify files until the proposed change has been reviewed.

When implementation is approved, keep the change focused. Do not
refactor unrelated Django/Oscar code.

## Suggested opening prompt for a new Codex thread

Use:

> Read `docs/TSHIRT_PREVIEW_CURRENT_STATE.md` completely. Then inspect
> the current files it references, especially `topository_01/views.py`
> and `utils/build_tshirt_assets.py`. We are currently fixing
> colour-dependent T-shirt fabric rendering: very light colours have
> excessive dark shadows, while dark colours develop whitish/chalky
> highlight spots. Summarise the actual current implementation and
> propose the smallest coherent fix. Do not modify any files yet.
