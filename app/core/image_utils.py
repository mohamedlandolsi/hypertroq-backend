"""
Image processing utilities.

Provides functions for resizing, compressing, and optimizing images
for efficient storage and delivery.
"""

import io
import logging
from typing import BinaryIO, Tuple

from PIL import Image

logger = logging.getLogger(__name__)


class ImageProcessingError(Exception):
    """Exception raised for image processing errors."""
    pass


def resize_image(
    image_content: bytes,
    max_width: int = 800,
    max_height: int = 800,
    maintain_aspect_ratio: bool = True,
) -> bytes:
    """Resize image to maximum dimensions while maintaining aspect ratio.
    
    Args:
        image_content: Original image bytes
        max_width: Maximum width in pixels (default: 800)
        max_height: Maximum height in pixels (default: 800)
        maintain_aspect_ratio: Whether to maintain aspect ratio (default: True)
        
    Returns:
        bytes: Resized image data
        
    Raises:
        ImageProcessingError: If image cannot be processed
        
    Examples:
        >>> with open("image.jpg", "rb") as f:
        ...     original = f.read()
        >>> resized = resize_image(original, max_width=400, max_height=400)
    """
    try:
        # Open image from bytes
        image = Image.open(io.BytesIO(image_content))
        
        # Convert RGBA to RGB if necessary (for JPEG compatibility)
        if image.mode == "RGBA":
            # Create white background
            background = Image.new("RGB", image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3])  # Use alpha channel as mask
            image = background
        elif image.mode not in ("RGB", "L"):
            # Convert other modes to RGB
            image = image.convert("RGB")
        
        # Get current dimensions
        width, height = image.size
        
        # Check if resizing is needed
        if width <= max_width and height <= max_height:
            logger.info(f"Image already within bounds ({width}x{height}), no resize needed")
            return image_content
        
        # Calculate new dimensions
        if maintain_aspect_ratio:
            # Calculate aspect ratio
            aspect_ratio = width / height
            
            # Determine new dimensions
            if width > height:
                new_width = min(width, max_width)
                new_height = int(new_width / aspect_ratio)
            else:
                new_height = min(height, max_height)
                new_width = int(new_height * aspect_ratio)
            
            # Ensure we don't exceed max dimensions
            if new_width > max_width:
                new_width = max_width
                new_height = int(new_width / aspect_ratio)
            if new_height > max_height:
                new_height = max_height
                new_width = int(new_height * aspect_ratio)
        else:
            new_width = min(width, max_width)
            new_height = min(height, max_height)
        
        # Resize image using high-quality Lanczos resampling
        resized_image = image.resize(
            (new_width, new_height),
            Image.Resampling.LANCZOS
        )
        
        # Save to bytes
        output = io.BytesIO()
        resized_image.save(output, format="JPEG", quality=95)
        output.seek(0)
        
        logger.info(f"Image resized from {width}x{height} to {new_width}x{new_height}")
        
        return output.read()
        
    except Exception as e:
        logger.error(f"Failed to resize image: {str(e)}")
        raise ImageProcessingError(f"Image resize failed: {str(e)}")


def compress_image(
    image_content: bytes,
    quality: int = 85,
    output_format: str = "JPEG",
) -> bytes:
    """Compress image to reduce file size.
    
    Args:
        image_content: Original image bytes
        quality: Compression quality (1-95, default: 85)
        output_format: Output format (JPEG, PNG, WEBP, default: JPEG)
        
    Returns:
        bytes: Compressed image data
        
    Raises:
        ImageProcessingError: If image cannot be processed
        ValueError: If quality or format is invalid
        
    Examples:
        >>> with open("image.jpg", "rb") as f:
        ...     original = f.read()
        >>> compressed = compress_image(original, quality=80)
    """
    # Validate quality
    if not 1 <= quality <= 95:
        raise ValueError("Quality must be between 1 and 95")
    
    # Validate format
    valid_formats = {"JPEG", "PNG", "WEBP"}
    output_format = output_format.upper()
    if output_format not in valid_formats:
        raise ValueError(f"Output format must be one of: {', '.join(valid_formats)}")
    
    try:
        # Open image from bytes
        image = Image.open(io.BytesIO(image_content))
        
        # Convert to RGB for JPEG/WEBP (required)
        if output_format in ("JPEG", "WEBP"):
            if image.mode == "RGBA":
                # Create white background
                background = Image.new("RGB", image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[3])
                image = background
            elif image.mode not in ("RGB", "L"):
                image = image.convert("RGB")
        
        # Compress and save to bytes
        output = io.BytesIO()
        
        if output_format == "JPEG":
            image.save(
                output,
                format="JPEG",
                quality=quality,
                optimize=True,
                progressive=True,
            )
        elif output_format == "PNG":
            image.save(
                output,
                format="PNG",
                optimize=True,
            )
        elif output_format == "WEBP":
            image.save(
                output,
                format="WEBP",
                quality=quality,
                method=4,  # Slower but better compression
            )
        
        output.seek(0)
        compressed_data = output.read()
        
        # Calculate compression ratio
        original_size = len(image_content)
        compressed_size = len(compressed_data)
        ratio = (1 - compressed_size / original_size) * 100
        
        logger.info(
            f"Image compressed: {original_size} -> {compressed_size} bytes "
            f"({ratio:.1f}% reduction)"
        )
        
        return compressed_data
        
    except Exception as e:
        logger.error(f"Failed to compress image: {str(e)}")
        raise ImageProcessingError(f"Image compression failed: {str(e)}")


def optimize_profile_image(image_content: bytes) -> Tuple[bytes, dict]:
    """Optimize image for profile picture use.
    
    Combines resizing and compression optimized for profile pictures.
    Target: 800x800 max, 85% quality JPEG, < 500KB
    
    Args:
        image_content: Original image bytes
        
    Returns:
        tuple: (optimized_image_bytes, metadata_dict)
        
    Raises:
        ImageProcessingError: If image cannot be processed
        
    Examples:
        >>> with open("avatar.jpg", "rb") as f:
        ...     original = f.read()
        >>> optimized, metadata = optimize_profile_image(original)
        >>> print(f"Size: {metadata['final_size_kb']:.1f} KB")
    """
    original_size = len(image_content)
    
    try:
        # Step 1: Resize to max 800x800
        resized = resize_image(
            image_content,
            max_width=800,
            max_height=800,
            maintain_aspect_ratio=True,
        )
        
        # Step 2: Compress with 85% quality
        optimized = compress_image(
            resized,
            quality=85,
            output_format="JPEG",
        )
        
        # Calculate metadata
        final_size = len(optimized)
        reduction = (1 - final_size / original_size) * 100
        
        # Get dimensions
        image = Image.open(io.BytesIO(optimized))
        width, height = image.size
        
        metadata = {
            "original_size_kb": original_size / 1024,
            "final_size_kb": final_size / 1024,
            "reduction_percent": reduction,
            "width": width,
            "height": height,
            "format": "JPEG",
        }
        
        logger.info(
            f"Profile image optimized: "
            f"{original_size/1024:.1f}KB -> {final_size/1024:.1f}KB "
            f"({reduction:.1f}% reduction), {width}x{height}"
        )
        
        return optimized, metadata
        
    except Exception as e:
        logger.error(f"Failed to optimize profile image: {str(e)}")
        raise ImageProcessingError(f"Profile image optimization failed: {str(e)}")


def get_image_info(image_content: bytes) -> dict:
    """Get information about an image.
    
    Args:
        image_content: Image bytes
        
    Returns:
        dict: Image information (format, mode, size, dimensions)
        
    Raises:
        ImageProcessingError: If image cannot be read
        
    Examples:
        >>> with open("image.jpg", "rb") as f:
        ...     data = f.read()
        >>> info = get_image_info(data)
        >>> print(f"Format: {info['format']}, Size: {info['width']}x{info['height']}")
    """
    try:
        image = Image.open(io.BytesIO(image_content))
        
        return {
            "format": image.format,
            "mode": image.mode,
            "size_bytes": len(image_content),
            "size_kb": len(image_content) / 1024,
            "width": image.size[0],
            "height": image.size[1],
        }
        
    except Exception as e:
        logger.error(f"Failed to get image info: {str(e)}")
        raise ImageProcessingError(f"Image info extraction failed: {str(e)}")


def validate_image(image_content: bytes, max_size_mb: int = 5) -> bool:
    """Validate image file.
    
    Args:
        image_content: Image bytes to validate
        max_size_mb: Maximum size in MB (default: 5)
        
    Returns:
        bool: True if valid
        
    Raises:
        ImageProcessingError: If image is invalid with reason
        
    Examples:
        >>> with open("image.jpg", "rb") as f:
        ...     data = f.read()
        >>> if validate_image(data, max_size_mb=10):
        ...     print("Image is valid")
    """
    # Check size
    size_mb = len(image_content) / (1024 * 1024)
    if size_mb > max_size_mb:
        raise ImageProcessingError(
            f"Image too large: {size_mb:.1f}MB (max: {max_size_mb}MB)"
        )
    
    # Check if it's a valid image
    try:
        image = Image.open(io.BytesIO(image_content))
        image.verify()  # Verify image integrity
        
        # Check for minimum dimensions
        width, height = image.size
        if width < 50 or height < 50:
            raise ImageProcessingError(
                f"Image too small: {width}x{height} (min: 50x50)"
            )
        
        return True
        
    except Exception as e:
        logger.error(f"Image validation failed: {str(e)}")
        raise ImageProcessingError(f"Invalid image: {str(e)}")
