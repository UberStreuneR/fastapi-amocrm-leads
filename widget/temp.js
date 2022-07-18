var data = {
  companyFields: [
    { value: "1", label: "Email" },
    { value: "2", label: "Web" },
    { value: "3", label: "Адрес" },
    { value: "4", label: "Примечание" },
    { value: "5", label: "Почтовый адрес" },
    { value: "6", label: "Последняя оплата" },
    { value: "7", label: "Уровень компании" },
    { value: "8", label: "Сумма оплат за 6 мес." },
  ],
  leadFields: [
    { value: "1", label: "Сообщ. в Телеграм" },
    { value: "2", label: "Кол-во успешных сделок за 6 мес." },
    { value: "3", label: "на дату" },
    { value: "4", label: "Этап 'Завершены работы'" },
    { value: "5", label: "Сделка для возврата залога?" },
    { value: "6", label: "Воронка Первичное этап Закрыто" },
  ],
  contactFields: [
    { value: "1", label: "Примечание" },
    { value: "2", label: "Регион" },
    { value: "3", label: "Уровень контакта" },
    { value: "4", label: "Кол-во успешных сделок за 6 мес." },
    { value: "5", label: "roistat" },
  ],
  dependencyType: [
    { value: "1", label: "От количества" },
    { value: "2", label: "От суммы" },
  ],
  entityType: [
    { value: "contact", label: "Контакт" },
    { value: "company", label: "Компания" },
  ],
};

define(["./templates.js"], function (templatesRenderer) {
  class Widget {
    constructor(widget, getTemplate) {
      this.widget = widget;
      this.getTemplate = getTemplate;
      this.isDestroyed = false;
    }

    optionsToItems({ options, values, prefix } = {}) {
      return options.reduce((items, option) => {
        let item = { id: option.value, option: option.label };

        if (values && prefix) {
          item.name = `${prefix}${option.value}`;
          item.is_checked = values.includes(option.value);
          item.option = `${option.group}. ${item.option}`;
        }

        items.push(item);
        return items;
      }, []);
    }

    pretendToRender() {
      alert("Let's say this was a render");
    }

    alertSomeShit() {
      alert("God this is awfull");
      this.pretendToRender();
    }

    renderPage = callback => {
      let $page = $("#work_area");
      this.getTemplate("entirety").then(entireTemplate => {
        alert("Started rendering");
        $page.append($(entireTemplate.render()));
        alert("Stopped rendering");
        callback();
      });
    };

    superMegaInit() {
      alert("Going to call the main render function now");
      this.renderPage(() => {
        alert("Going to search for status-tab now");
        var statusTab = document.querySelector("#status-tab");
        alert(statusTab);
        statusTab.innerHTML = "<p>HelloWorld</p>";
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
        widget.superMegaInit();
        return true;
      },
      render: () => true,
      bind_actions: function () {
        return true;
      },
      destroy: () => widget.destroy(),
      onSave: () => true,
    };
    return this;
  };
});
