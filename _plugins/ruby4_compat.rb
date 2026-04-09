# Monkey-patch for Ruby 3.2+ compatibility with Jekyll 3.9 / Liquid 4.0
# tainted?/taint/untaint were removed in Ruby 3.2 but Liquid 4.0 still calls them.
unless Object.method_defined?(:tainted?)
  class Object
    def tainted?
      false
    end

    def taint
      self
    end

    def untaint
      self
    end
  end
end
