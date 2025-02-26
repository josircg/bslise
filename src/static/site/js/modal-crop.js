/*
 This code uses cropper.js in a bootstrap modal
 Depends on jquery, jquery-ui, jquery.ui.touch-punch, cropper, jquery-cropper and _crop_zone.html
*/
(function ($) {
    $(document).ready(function () {
        // Current input file
        let $imgSelected;
        // Option to define cropper width: 0 = 600 x 400 - 1 = 1100 x 400
        let imgWidthOption;
        // Inputs defined on _crop_zone.html
        let $image = $("#image");
        let $modalCrop = $("#modalCrop");
        // Inputs that hold information about original image and cropped image result
        let $images = $('.fileinput');

        $images.each(function () {
            let inputid = this.id;
            // Binds on change function to each input target marked as image result
            $('#imageResult' + $(this).data('image-suffix')).click(function () {
                $(`#${inputid}`).trigger('change');
            });
        });

        // SCRIPT TO OPEN THE MODAL WITH THE PREVIEW
        $images.change(function () {
            $imgSelected = $(this);
            imgWidthOption = $imgSelected.data('image-width-option');

            if (this.files && this.files[0]) {
                let reader = new FileReader();
                reader.onload = function (e) {
                    $image.attr("src", e.target.result);
                    $modalCrop.modal("show");
                }
                reader.readAsDataURL(this.files[0]);
            }
        });

        // SCRIPTS TO HANDLE THE CROPPER BOX
        $modalCrop.on("shown.bs.modal", function () {
            $image.cropper({
                viewMode: 0,
                autoCropArea: 1,
                aspectRatio: imgWidthOption === 1 ? 11 / 4 : 3 / 2,
                dragMode: 'move',
                fillColor: '#000000',
                toggleDragModeOnDblclick: false,
            });
        }).on("hidden.bs.modal", function () {
            $image.cropper("destroy");
        });

        // Zoom in button
        $("#zoom-in").click(function () {
            $image.cropper('zoom', 0.01);  // Aumenta o zoom em 1%
        });
        // Zoom out button
        $("#zoom-out").click(function () {
            $image.cropper('zoom', -0.01);  // Diminui o zoom em 1%
        });
        $("#fill").click(function () {
            $image.cropper('getCroppedCanvas', {fillColor: '#000000'})
        });

        // Zoom reset button
        $('#zoom-reset').click(function () {
            $image.cropper('reset'); // Reseta o zoom para o estado original
        });
        // SCRIPT TO COLLECT THE DATA AND POST TO THE SERVER
        $(".js-crop-and-upload").click(function () {
            let cropData = $image.cropper("getData");
            let suffix = $imgSelected.data('image-suffix');
            $("#id_x" + suffix).val(cropData["x"]);
            $("#id_y" + suffix).val(cropData["y"]);
            $("#id_height" + suffix).val(cropData["height"]);
            $("#id_width" + suffix).val(cropData["width"]);

            $modalCrop.modal("hide");

            $('#imageResult' + suffix).attr('src', $image.cropper('getCroppedCanvas',
                {width: imgWidthOption === 1 ? 1100 : 600, height: 400}).toDataURL());
        });
    });
})(jQuery);