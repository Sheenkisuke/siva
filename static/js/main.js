document.addEventListener('DOMContentLoaded', () => {
    // --- Sidebar Toggle ---
    const mobileToggle = document.getElementById('mobile-toggle');
    const sidebar = document.getElementById('sidebar');
    const sidebarOverlay = document.getElementById('sidebar-overlay');

    if (mobileToggle && sidebar && sidebarOverlay) {
        const toggleSidebar = () => {
            sidebar.classList.toggle('active');
        };

        mobileToggle.addEventListener('click', toggleSidebar);
        sidebarOverlay.addEventListener('click', toggleSidebar);
    }

    // --- Flash Messages Auto-dismiss ---
    const flashMessages = document.querySelectorAll('.alert');
    flashMessages.forEach(alert => {
        const closeBtn = alert.querySelector('.alert-close');
        
        const dismissAlert = () => {
            alert.style.animation = 'fadeOut 0.3s ease forwards';
            setTimeout(() => alert.remove(), 300);
        };

        if (closeBtn) {
            closeBtn.addEventListener('click', dismissAlert);
        }

        // Auto dismiss after 5 seconds
        setTimeout(dismissAlert, 5000);
    });

    // --- Password Toggle ---
    const passwordToggle = document.querySelector('.password-toggle');
    const passwordInput = document.getElementById('password');
    if (passwordToggle && passwordInput) {
        passwordToggle.addEventListener('click', () => {
            const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
            passwordInput.setAttribute('type', type);
            passwordToggle.textContent = type === 'password' ? '👁️' : '🙈';
        });
    }

    // --- Modal Logic ---
    const forgotPasswordLink = document.getElementById('forgot-password-link');
    const modalOverlay = document.getElementById('forgot-password-modal');
    if (forgotPasswordLink && modalOverlay) {
        const closeModalBtn = modalOverlay.querySelector('.btn');
        
        forgotPasswordLink.addEventListener('click', (e) => {
            e.preventDefault();
            modalOverlay.classList.add('active');
        });

        closeModalBtn.addEventListener('click', () => {
            modalOverlay.classList.remove('active');
        });

        modalOverlay.addEventListener('click', (e) => {
            if (e.target === modalOverlay) {
                modalOverlay.classList.remove('active');
            }
        });
    }

    // --- Photo Upload Logic ---
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('foto-upload');
    const previewImg = document.getElementById('preview-img');
    const dropContent = document.getElementById('drop-content');
    const uploadForm = document.getElementById('upload-form');
    const loadingOverlay = document.getElementById('loading-overlay');
    const loadingMessage = document.getElementById('loading-message');

    if (dropZone && fileInput && previewImg) {
        const handleFile = (file) => {
            if (!file.type.match('image.*')) {
                alert('Por favor seleccione una imagen (JPG o PNG).');
                return;
            }

            if (file.size > 5 * 1024 * 1024) {
                alert('El archivo es demasiado grande. Máximo 5MB.');
                return;
            }

            const reader = new FileReader();
            reader.onload = (e) => {
                // Client-side dimension check simulation (actual check usually requires loading img object)
                const img = new Image();
                img.onload = () => {
                    // We log dimensions but don't strictly block here to allow server AI validation to handle it
                    console.log(`Dimensiones de imagen: ${img.width}x${img.height}`);
                    
                    previewImg.src = e.target.result;
                    previewImg.style.display = 'block';
                    if(dropContent) dropContent.style.display = 'none';
                };
                img.src = e.target.result;
            };
            reader.readAsDataURL(file);
        };

        dropZone.addEventListener('click', () => fileInput.click());

        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });

        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('dragover');
        });

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            if (e.dataTransfer.files.length) {
                fileInput.files = e.dataTransfer.files;
                handleFile(e.dataTransfer.files[0]);
            }
        });

        fileInput.addEventListener('change', function() {
            if (this.files.length) {
                handleFile(this.files[0]);
            }
        });
        
        if(uploadForm) {
            uploadForm.addEventListener('submit', (e) => {
                if(!fileInput.files.length) {
                    e.preventDefault();
                    alert('Debe seleccionar una fotografía para continuar.');
                    return;
                }
                
                if(loadingOverlay) {
                    loadingOverlay.classList.add('active');
                    
                    // Simulate progressive loading messages
                    setTimeout(() => {
                        if(loadingMessage) loadingMessage.textContent = 'Verificando requisitos de la foto (Fondo, Iluminación)...';
                    }, 1500);
                    
                    setTimeout(() => {
                        if(loadingMessage) loadingMessage.textContent = 'Verificando identidad mediante reconocimiento facial...';
                    }, 3500);
                }
            });
        }
    }

    // --- Generic Form Loading ---
    const forms = document.querySelectorAll('form:not(#upload-form)');
    forms.forEach(form => {
        form.addEventListener('submit', () => {
            if(loadingOverlay && !loadingOverlay.classList.contains('active')) {
                loadingOverlay.classList.add('active');
                if(loadingMessage) loadingMessage.textContent = 'Procesando solicitud...';
            }
        });
    });
});
