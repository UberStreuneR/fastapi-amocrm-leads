define(["./templates.js"], function (templatesRenderer) {
  class Widget {
    constructor(widget, getTemplate) {
      this.widget = widget;
      this.getTemplate = getTemplate;
      this.isDestroyed = false;
    }

    renderAmountPage() {
      this.getTemplate("amount").then(amountTemplate => {
        let $title = $(".content__top__preset");
        let $actions = $(".list__body-right__top");
        let $page = $("#work_area");
        $title.text("Test");
        $page.append($(amountTemplate.render()));
      });
    }

    destroy() {
      this.isDestroyed = true;
    }
  }

  return function () {
    let self = this;
    let widget = new Widget(this, templatesRenderer(this));
    // var getTemplate = templatesRenderer(this);
    this.callbacks = {
      init: function () {
        return true;
      },
      advancedSettings: function () {
        $("#list_page_holder").html("Настройки виджета здесь");
        // widget.renderAmountPage();
        return true;
      },
      render: () => true,
      bind_actions: function () {
        return true;
      },
      destroy: () => widget.destroy(),
    };
    return this;
  };
});
