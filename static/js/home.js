$(function(){

  var Task = Backbone.Model.extend({

    defaults: function() {
      return {
        title: "empty todo...",
        done: false,
        day: "Today",
        planned: "Today"
      };
    },

    // Toggle the `done` state of this todo item.
    toggle: function() {
      this.save({done: !this.get("done")});
    }

  });

  var Plan = Backbone.Model.extend({

    defaults: function() {
      return{
        task: "Herp",
      }
    }
  });

  var Day = Backbone.Model.extend({

    defaults: function(){
      return{
        day: "Someday",
        tasks: []
      }
    }

  });

  var Planner = Backbone.Model.extend({

    defaults: function(){
      return{
        day: "Someday",
        plans: []
      }
    }

  })

  var TaskView = Backbone.View.extend({
    el: $(".task")
    template: _.template($('#task-template').html()),
    events: {
      "click .toggle"   : "toggleDone",
      "click a.destroy" : "clear",
      "keypress .edit"  : "updateOnEnter",
      "blur .edit"      : "close",
      "dblclick .view"  : "edit"
      // "drag" : "move"
    },
    initialize: function() {
      this.listenTo(this.model, 'change', this.render);
      this.listenTo(this.model, 'destroy', this.remove);
    },
    render: function() {
      this.$el.html(this.template(this.model.toJSON()));
      this.$el.toggleClass('done', this.model.get('done'));
      this.input = this.$('.edit');
      return this;
    },

    toggleDone: function() {
      this.model.toggle();
    },

    // Switch this view into `"editing"` mode, displaying the input field.
    edit: function() {
      this.$el.addClass("editing");
      this.input.focus();
    },

    // Close the `"editing"` mode, saving changes to the todo.
    close: function() {
      var value = this.input.val();
      if (!value) {
        this.clear();
      } else {
        this.model.save({title: value});
        this.$el.removeClass("editing");
      }
    },

    // If you hit `enter`, we're through editing the item.
    updateOnEnter: function(e) {
      if (e.keyCode == 13) this.close();
    },

    // Remove the item, destroy the model.
    clear: function() {
      this.model.destroy();
    }

    move: function(){

    }

  });

  var PlanView = Backbone.View.extend({
    el: $(".plan")

    events: {
      "click .toggle" : "toggleDone"
      // "drag" : "move"
    }
    initialize: function(){

    }
    render: function(){

    }
    toggleDone: function(){

    }
    move: function(){

    }
  })

  var DayView = Backbone.View.extend({
    el: $(".day")

    initialize: function(){

    }
    render: function(){

    }
  })

  var PlannerView = Backbone.View.extend({
    el: $(".day")

    initialize: function(){

    }
    render: function(){

    }
  })

  var UniversalInput = Backbone.View.extend({

    el: $("#universal"),

    events: {
      "keypress #new-todo":  "createOnEnter",
    },

    initialize: function() {
      this.input = this.$("#new-todo");
    },

    // Add a single todo item to the list by creating a view for it, and
    // appending its element to the `<ul>`.
    addOne: function(todo) {
      var view = new TodoView({model: todo});
      this.$("#todo-list").append(view.render().el);
    },

    // If you hit return in the main input field, create new **Todo** model,
    // persisting it to *localStorage*.
    createOnEnter: function(e) {
      if (e.keyCode != 13) return;
      if (!this.input.val()) return;

      Todos.create({title: this.input.val()});
      this.input.val('');
    },
  });
});