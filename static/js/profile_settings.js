// Profile Settings page JS - encapsulated to avoid global scope pollution
(function () {
  let cropper = null;
  let selectedFile = null;

  function handleCancelVerification() {
    if (!confirm('Bạn có chắc muốn hủy bỏ thay đổi đang chờ xác thực?')) return;
    fetch(window.location.href, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: 'cancel_verification=1'
    }).then(r => { if (r.ok) window.location.reload(); })
      .catch(err => {
        console.error('Error canceling verification:', err);
        alert('Có lỗi xảy ra khi hủy bỏ xác thực. Vui lòng thử lại.');
      });
  }

  function openCropper(input) {
    if (!(input && input.files && input.files[0])) return;
    const file = input.files[0];
    const maxSize = 5 * 1024 * 1024; // 5MB
    if (file.size > maxSize) { alert('File quá lớn! Vui lòng chọn file nhỏ hơn 5MB.'); input.value=''; return; }
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif'];
    if (!allowedTypes.includes(file.type)) { alert('Chỉ chấp nhận file ảnh: JPG, PNG, GIF'); input.value=''; return; }
    selectedFile = file;
    const reader = new FileReader();
    reader.onload = function(e){
      const img = document.getElementById('cropper-image');
      img.src = e.target.result;
      document.getElementById('avatar-cropper-modal').classList.add('show');
      if (cropper) cropper.destroy();
      cropper = new Cropper(img, {
        aspectRatio: 1,
        viewMode: 0,
        dragMode: 'move',
        background: false,
        guides: true,
        center: false,
        autoCropArea: 0.8,
        movable: true,
        zoomable: true,
        rotatable: false,
        scalable: false,
        cropBoxResizable: true,
        cropBoxMovable: true,
        minContainerWidth: 280,
        minContainerHeight: 280,
        minCropBoxWidth: 100,
        minCropBoxHeight: 100,
        maxCropBoxWidth: 280,
        maxCropBoxHeight: 280,
        checkCrossOrigin: false,
        checkOrientation: false,
        modal: false,
        highlight: true,
        background: true,
        autoCrop: true,
        responsive: true,
        restore: false,
        checkImageUrl: false,
        ready: function() {
          // Set initial crop box size to be smaller for better UX
          const containerData = cropper.getContainerData();
          const initialSize = Math.min(containerData.width, containerData.height) * 0.7;
          cropper.setCropBoxData({
            left: (containerData.width - initialSize) / 2,
            top: (containerData.height - initialSize) / 2,
            width: initialSize,
            height: initialSize
          });
        },
        cropmove: function(event) {
          // Allow free movement and resizing
          return true;
        },
        cropstart: function(event) {
          // Allow all crop operations
          return true;
        },
        cropend: function(event) {
          // Ensure crop box stays within bounds with proper spacing
          const cropBoxData = cropper.getCropBoxData();
          const containerData = cropper.getContainerData();
          const minSpacing = 10;
          
          // Check if crop box is too close to edges
          if (cropBoxData.left < minSpacing || 
              cropBoxData.top < minSpacing ||
              cropBoxData.left + cropBoxData.width > containerData.width - minSpacing ||
              cropBoxData.top + cropBoxData.height > containerData.height - minSpacing) {
            
            // Adjust crop box to stay within bounds
            const newLeft = Math.max(minSpacing, Math.min(cropBoxData.left, containerData.width - cropBoxData.width - minSpacing));
            const newTop = Math.max(minSpacing, Math.min(cropBoxData.top, containerData.height - cropBoxData.height - minSpacing));
            
            cropper.setCropBoxData({
              left: newLeft,
              top: newTop
            });
          }
        }
      });
    };
    reader.readAsDataURL(file);
  }

  function closeCropper(){
    document.getElementById('avatar-cropper-modal').classList.remove('show');
    if (cropper) cropper.destroy();
    cropper = null;
    selectedFile = null;
    const input = document.getElementById('avatar-input');
    if (input) input.value = '';
  }

  // Debug function to check cropper state
  function debugCropperState() {
    if (!cropper) {
      console.log('❌ Cropper not initialized');
      return;
    }
    
    const containerData = cropper.getContainerData();
    const cropBoxData = cropper.getCropBoxData();
    const canvasData = cropper.getCanvasData();
    
    console.log('🔍 Cropper Debug Info:');
    console.log('Container:', containerData);
    console.log('CropBox:', cropBoxData);
    console.log('Canvas:', canvasData);
    console.log('Min crop size:', cropper.options.minCropBoxWidth, 'x', cropper.options.minCropBoxHeight);
    console.log('Max crop size:', cropper.options.maxCropBoxWidth, 'x', cropper.options.maxCropBoxHeight);
    console.log('CropBox resizable:', cropper.options.cropBoxResizable);
    console.log('CropBox movable:', cropper.options.cropBoxMovable);
  }

  function handleCropAndAttach(){
    if (!cropper) return;
    const canvas = cropper.getCroppedCanvas({ width: 300, height: 300, imageSmoothingQuality: 'high' });
    const circleCanvas = document.createElement('canvas');
    circleCanvas.width = 300; circleCanvas.height = 300;
    const ctx = circleCanvas.getContext('2d');
    ctx.save(); ctx.beginPath(); ctx.arc(150,150,150,0,2*Math.PI); ctx.closePath(); ctx.clip();
    ctx.drawImage(canvas,0,0,300,300); ctx.restore();
    const avatarPreview = document.getElementById('avatar-preview');
    if (avatarPreview) {
      avatarPreview.src = circleCanvas.toDataURL('image/png');
    } else {
      const avatarPlaceholder = document.getElementById('avatar-placeholder');
      if (avatarPlaceholder) {
        const newImg = document.createElement('img');
        newImg.src = circleCanvas.toDataURL('image/png');
        newImg.alt = 'Avatar Preview';
        newImg.className = 'avatar';
        newImg.id = 'avatar-preview';
        avatarPlaceholder.parentNode.replaceChild(newImg, avatarPlaceholder);
      }
    }
    circleCanvas.toBlob(function(blob){
      let hiddenInput = document.getElementById('avatar-cropped-blob');
      if (!hiddenInput) {
        hiddenInput = document.createElement('input');
        hiddenInput.type = 'hidden';
        hiddenInput.name = 'avatar_cropped';
        hiddenInput.id = 'avatar-cropped-blob';
        document.querySelector('form').appendChild(hiddenInput);
      }
      const reader = new FileReader();
      reader.onloadend = function(){ hiddenInput.value = reader.result; };
      reader.readAsDataURL(blob);
    }, 'image/png');
    closeCropper();
  }

  // Suppress deprecated MutationEvents globally (kept from inline script)
  (function suppressDeprecatedMutationEvents(){
    const originalAddEventListener = EventTarget.prototype.addEventListener;
    EventTarget.prototype.addEventListener = function(type, listener, options) {
      if (type === 'DOMNodeInserted' || type === 'DOMNodeRemoved' || type === 'DOMSubtreeModified') {
        return;
      }
      return originalAddEventListener.call(this, type, listener, options);
    };
  })();

  document.addEventListener('DOMContentLoaded', function () {
    // Initialize Navigation component
    if (window.NavigationComponent && typeof window.NavigationComponent.init === 'function') {
      window.NavigationComponent.init();
    }

    // Quill init
    let quill;
    const bioEditor = document.getElementById('bio-editor');
    if (bioEditor) {
      quill = new Quill('#bio-editor', {
        theme: 'snow',
        modules: {
          toolbar: [
            ['bold', 'italic', 'underline', 'strike'],
            [{ 'header': [1, 2, 3, false] }],
            [{ list: 'ordered' }, { list: 'bullet' }],
            [{ 'align': [] }],
            [{ color: ['#ffffff','#ffeb3b','#ff9800','#ff5722','#e91e63','#9c27b0','#673ab7','#3f51b5','#2196f3','#00bcd4','#009688','#4caf50','#8bc34a','#cddc39','#ffc107','#ff9800','#795548','#9e9e9e','#607d8b'] }],
            ['clean']
          ]
        },
        placeholder: 'Viết gì đó về bản thân...'
      });
      // Sync content on text changes
      quill.on('text-change', function () {
        const bioHidden = document.getElementById('bio-hidden');
        if (bioHidden) bioHidden.value = quill.root.innerHTML;
      });
      
      // FIX: Sync initial content immediately after initialization
      const bioHidden = document.getElementById('bio-hidden');
      if (bioHidden) {
        bioHidden.value = quill.root.innerHTML;
        console.log('🔄 Initial Quill content synced:', bioHidden.value.substring(0, 50) + '...');
      }
      
      console.log('✅ Quill initialized for bio editor');
    }

    // Verification helpers in page scope
    function showVerificationForm() {
      const sec = document.getElementById('verification-section');
      if (sec) sec.classList.add('show');
      const sb = document.getElementById('save-button-section');
      if (sb) sb.style.display = 'none';
      const code = document.getElementById('verification_code');
      if (code) code.focus();
    }
    function hideVerificationForm() {
      const sec = document.getElementById('verification-section');
      if (sec) sec.classList.remove('show');
      const sb = document.getElementById('save-button-section');
      if (sb) sb.style.display = 'block';
      const code = document.getElementById('verification_code');
      if (code) code.value = '';
    }

    // Show form if a flash mentions verification
    const flashMessages = document.querySelectorAll('.flash');
    flashMessages.forEach(function(message) {
      if (message.textContent.includes('mã xác thực')) {
        showVerificationForm();
      }
    });

    // Bind inputs and buttons
    const verificationInput = document.getElementById('verification_code');
    if (verificationInput) {
      verificationInput.addEventListener('input', function() {
        this.value = this.value.replace(/[^0-9]/g, '');
      });
    }

    const fileInput = document.getElementById('avatar-input');
    if (fileInput) fileInput.addEventListener('change', function(){ openCropper(this); });

    const cropBtn = document.getElementById('crop-avatar-btn');
    if (cropBtn) cropBtn.addEventListener('click', handleCropAndAttach);

    const closeBtn = document.getElementById('close-cropper-btn');
    if (closeBtn) closeBtn.addEventListener('click', closeCropper);

    const cancelBtn = document.getElementById('cancel-verification-btn');
    if (cancelBtn) cancelBtn.addEventListener('click', handleCancelVerification);

    // Add debug event listeners for cropper
    document.addEventListener('keydown', function(e) {
      // Press 'D' key to debug cropper state
      if (e.key === 'd' || e.key === 'D') {
        debugCropperState();
      }
    });

    // FIX: Sync Quill content before form submission
    const form = document.querySelector('form');
    if (form && quill) {
      form.addEventListener('submit', function(e) {
        const bioHidden = document.getElementById('bio-hidden');
        if (bioHidden && quill) {
          bioHidden.value = quill.root.innerHTML;
          console.log('🔄 Synced Quill content before submit:', bioHidden.value.substring(0, 100) + '...');
        }
      });
    }
  });
})();


