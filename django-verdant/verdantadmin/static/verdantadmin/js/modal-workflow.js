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

    container = $('<div class="modal fade" tabindex="-1" role="dialog" aria-hidden="true">\n    <div class="modal-dialog">\n        <div class="modal-content">\n            <button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button>\n            <div class="modal-body">\n                <p>ERMERGERD! MERDERLS!</p>\n            </div>\n        </div><!-- /.modal-content -->\n    </div><!-- /.modal-dialog -->\n</div>');

    $('body').append(container);
    container.modal();

    return self;
}
