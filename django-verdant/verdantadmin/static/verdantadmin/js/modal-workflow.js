/* A framework for modal popups that are loaded via AJAX, allowing navigation to other
subpages to happen within the lightbox, and returning a response to the calling page,
possibly after several navigation steps
*/

function ModalWorkflow(opts) {
    /* options passed in 'opts':
        'url' (required): initial 
        'responses' (optional): dict of callbacks to be called when the modal content
            calls modal.respond(callbackName, params)
    */

    var self = {};
    var responseCallbacks = opts.responses || {};

    var container = $('<div class="modal fade" tabindex="-1" role="dialog" aria-hidden="true">\n    <div class="modal-dialog">\n        <div class="modal-content">\n            <button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button>\n            <div class="modal-body"></div>\n        </div><!-- /.modal-content -->\n    </div><!-- /.modal-dialog -->\n</div>');
    $('body').append(container);
    container.modal();

    self.body = container.find('.modal-body');

    self.loadUrl = function(url, urlParams) {
        $.get(url, urlParams, self.loadResponseText, 'text');
    };

    self.loadResponseText = function(responseText) {
        var response = eval('(' + responseText + ')');
        self.loadBody(response);
    };

    self.loadBody = function(body) {
        if (body.html) {
            self.body.html(body.html);
        }
        if (body.onload) {
            body.onload(self);
        }
    };

    self.respond = function(responseType) {
        if (responseType in responseCallbacks) {
            args = Array.prototype.slice.call(arguments, 1);
            responseCallbacks[responseType].apply(self, args);
        }
    };

    self.close = function() {
        container.modal('hide');
    };

    self.loadUrl(opts.url, opts.urlParams);

    return self;
}
