/**
 * Load the given file to check whether this is a readable image.
 */
function checkImageFile(file, dfd, data) {

  var reader = new FileReader();
  var image  = new Image();

  reader.readAsDataURL(file);  
  reader.onload = function(_file) {
    image.src    = _file.target.result;
    image.onload = function() {
      dfd.resolveWith(this, [data]);
    };
    image.onerror= function() {
      file.error = 'Invalid file type.';
      dfd.rejectWith(this, [data]);
    };
  };
  
}

/**
 * Put our image validation in the jquery-fileupload processing queue
 */
$.blueimp.fileupload.prototype.processActions.validate = function (data, options) {
  if (options.disabled) {
    return data;
  }
  var dfd = $.Deferred(),
  file = data.files[data.index];
              
  if (!options.acceptFileTypes.test(file.type)) {
    file.error = 'Invalid file type.';
    dfd.rejectWith(this, [data]);
  } else {
    checkImageFile(file, dfd, data);
  }
  return dfd.promise();
};

function activateImageUpload(for_id) {

    // remember the original add function for later because we're going to overwrite it
    var originalAdd = $.blueimp.fileupload.prototype.options.add;
    var containerElement = $($('#' + for_id));
    var inputElement = containerElement.find('#id_' + for_id);

    // activate the file upload field
    $(inputElement).fileupload({
      dataType: 'json',
      imageMaxWidth: 800,
      imageMaxHeight: 800,
      imageMinWidth: 10,
      imageMinHeight: 10,

      acceptFileTypes: /(\.|\/)(gif|jpe?g|png)$/i,

      processfail: function (e, data) {
        alert('Could not upload ' + data.files[data.index].name + ': this file is not a valid image.');
      },
      add: function(e, data) {
        containerElement.find('#progress .bar').show();
        originalAdd.call(this, e, data);
      },
      done: function (e, data) {
    
        if (!data.result.ok)
        {
          alert("Could not upload the file. Please try again with a different file.");
        }
        else
        {
          containerElement.find('#progress .bar').hide();
          containerElement.find('#preview').html(data.files[0].preview);
          containerElement.find('#preview').append('<span>' + data.files[0].name + '</span>');
          containerElement.find('#preview').append('<div id="info-flash" style="z-index: 100; background-color: #FF7B0A; position: absolute; top: 0; left: 0; width: 100%; height: 100%; text-align: center; font-size: 250%;">Saved</div>');
          containerElement.find('#preview #info-flash').fadeOut(2000);
        }
      },
      fail: function (e, data) {
        alert("Could not upload the file: the server responded with an error.");
        containerElement.find('#progress .bar').hide();
      },
      progressall: function (e, data) {
        var progress = parseInt(data.loaded / data.total * 100, 10);
        containerElement.find('#progress .bar').css('width', progress + '%');
      }
    });
}


